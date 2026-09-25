"""MongoDB polling worker for asynchronous voice requests."""

import logging
import os
import time
import uuid

from pymongo import MongoClient, ReturnDocument

from src import config
from src.services import generate_and_merge_tts, upload_to_s3
from src.voices import resolve_voice

logger = logging.getLogger(__name__)

# Legacy producers omit status; newer producers may use 0 or pending.
_PENDING = {"$or": [
    {"status": {"$exists": False}}, {"status": None},
    {"status": "0"}, {"status": "pending"},
]}


def process_one(audios_collection, projects_collection) -> bool:
    """Atomically claim and process one queued job; return whether one was found."""
    document = audios_collection.find_one_and_update(
        _PENDING, {"$set": {"status": "1"}},
        sort=[("id", 1), ("_id", 1)], return_document=ReturnDocument.AFTER,
    )
    if document is None:
        return False

    job_id = document["_id"]
    output_path = None
    try:
        user_id = int(document.get("user_id"))
        if user_id <= 0:
            raise ValueError("user_id must be positive")
        text = document.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must not be empty")
        if len(text) > config.MAX_TEXT_LENGTH:
            raise ValueError(f"Text exceeds {config.MAX_TEXT_LENGTH} characters")
        language = config.SUPPORTED_LANGUAGES.get(str(document.get("language", "")).strip().upper())
        if language is None:
            raise ValueError("Unsupported language")
        speaker_path = resolve_voice(str(document.get("voice_id", "")))
        if speaker_path is None:
            raise ValueError("Unknown voice")

        audios_collection.update_one({"_id": job_id}, {"$set": {"status": "2"}})
        output_path = generate_and_merge_tts(text.strip(), speaker_path, language)
        audios_collection.update_one({"_id": job_id}, {"$set": {"status": "3"}})
        url = upload_to_s3(output_path, config.S3_BUCKET, f"output_{uuid.uuid4().hex}.mp3")

        projects_collection.update_one(
            {"user_id": user_id},
            {"$set": {"audio_link": url}, "$inc": {"edit_flag": 1}},
        )
        audios_collection.update_one(
            {"_id": job_id}, {"$set": {"status": "4", "audio_link": url}, "$unset": {"error": ""}},
        )
    except Exception as exc:
        logger.exception("Audio job %s failed", job_id)
        # Retain failed requests so they can be inspected and explicitly retried.
        audios_collection.update_one(
            {"_id": job_id}, {"$set": {"status": "failed", "error": str(exc)}},
        )
    finally:
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
    return True


def generate_audio(audios_collection, projects_collection):
    logger.info("Worker started")
    while True:
        try:
            if not process_one(audios_collection, projects_collection):
                time.sleep(config.WORKER_POLL_INTERVAL)
        except Exception:
            logger.exception("Worker polling failed")
            time.sleep(config.WORKER_POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with MongoClient(config.MONGO_URI) as client:
        db = client[config.MONGO_DB]
        generate_audio(db[config.MONGO_INPUTS_COLLECTION], db[config.MONGO_PROJECTS_COLLECTION])
