"""HTTP API for synchronous voice generation."""

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src import config
from src.services import generate_and_merge_tts, upload_to_s3
from src.voices import resolve_voice, voice_names

logger = logging.getLogger(__name__)
app = FastAPI(title="Voice Cloner API")


class TextInput(BaseModel):
    text: str
    name: str
    language: str


@app.get("/")
def root():
    return {"message": "Voice Cloner API is running."}


@app.get("/voices")
def voices():
    return {"voices": voice_names(), "languages": list(config.SUPPORTED_LANGUAGES)}


@app.post("/generate_tts")
def generate_tts(item: TextInput):
    text = item.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text must not be empty")
    if len(text) > config.MAX_TEXT_LENGTH:
        raise HTTPException(status_code=422, detail=f"Text exceeds {config.MAX_TEXT_LENGTH} characters")

    speaker_path = resolve_voice(item.name)
    if speaker_path is None:
        raise HTTPException(status_code=422, detail="Unknown voice; see GET /voices")
    language = config.SUPPORTED_LANGUAGES.get(item.language.strip().upper())
    if language is None:
        raise HTTPException(status_code=422, detail="Unsupported language; see GET /voices")

    output_path = None
    try:
        output_path = generate_and_merge_tts(text, speaker_path, language)
        url = upload_to_s3(output_path, config.S3_BUCKET, f"output_{uuid.uuid4().hex}.mp3")
    except Exception as exc:
        logger.exception("Voice generation failed")
        raise HTTPException(status_code=500, detail="Voice generation failed") from exc
    finally:
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
    return {"message": "Audio generated and uploaded to S3", "file_url": url}
