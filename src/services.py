"""Voice generation and storage."""

import os
import re
import tempfile

from pydub import AudioSegment

from src import config
from src.core import get_s3_client, get_tts_model, tts_lock


# Conservative character budgets help keep individual model calls manageable.
_LANG_CHAR_LIMIT = {"en": 200, "hi": 160}
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?।])\s+")


def split_text(text: str, max_length: int = 200) -> list[str]:
    """Prefer sentence boundaries, then words, then split an oversized word."""
    if max_length < 1:
        raise ValueError("max_length must be positive")
    sentences = _SENTENCE_SPLIT_RE.split(" ".join(text.split()))
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        if not sentence:
            continue
        for part in _wrap_words(sentence, max_length):
            candidate = f"{buffer} {part}" if buffer else part
            if len(candidate) <= max_length:
                buffer = candidate
            else:
                chunks.append(buffer)
                buffer = part
    if buffer:
        chunks.append(buffer)
    return chunks


def _wrap_words(sentence: str, max_length: int) -> list[str]:
    pieces: list[str] = []
    buffer = ""
    for word in sentence.split():
        if len(word) > max_length:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.extend(word[i:i + max_length] for i in range(0, len(word), max_length))
            continue
        candidate = f"{buffer} {word}" if buffer else word
        if len(candidate) <= max_length:
            buffer = candidate
        else:
            pieces.append(buffer)
            buffer = word
    if buffer:
        pieces.append(buffer)
    return pieces


def generate_and_merge_tts(text: str, audio_speaker_path: str, language: str) -> str:
    """Return a unique MP3 path; the caller must delete it after use."""
    if not os.path.isfile(audio_speaker_path):
        raise FileNotFoundError(f"Speaker sample not found: {audio_speaker_path}")
    if language not in _LANG_CHAR_LIMIT:
        raise ValueError(f"Unsupported language code: {language}")
    chunks = split_text(text, _LANG_CHAR_LIMIT[language])
    if not chunks:
        raise ValueError("Text must not be empty")

    with tempfile.TemporaryDirectory(prefix="voice_cloner_") as tmp_dir:
        paths = []
        # Coqui's model is shared by requests within the process.
        with tts_lock:
            model = get_tts_model()
            for index, chunk in enumerate(chunks):
                path = os.path.join(tmp_dir, f"chunk_{index}.wav")
                model.tts_to_file(
                    text=chunk, speaker_wav=audio_speaker_path,
                    language=language, file_path=path,
                )
                paths.append(path)

        merged = AudioSegment.empty()
        for path in paths:
            merged += AudioSegment.from_wav(path)

        fd, result_path = tempfile.mkstemp(prefix="voice_cloner_", suffix=".mp3")
        os.close(fd)
        try:
            merged.export(result_path, format="mp3")
        except Exception:
            os.unlink(result_path)
            raise
        return result_path


def upload_to_s3(file_path: str, bucket_name: str, object_name: str) -> str:
    """Upload MP3 audio and return a temporary download URL."""
    s3 = get_s3_client()
    s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={"ContentType": "audio/mpeg"})
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_name},
        ExpiresIn=config.PRESIGNED_URL_EXPIRY,
    )
