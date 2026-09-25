"""Discover available reference voice files."""
import os

from src import config

# Files in the voices dir that are outputs/artifacts, not speaker references.
def available_voices() -> dict:
    """Return a mapping of UPPERCASE voice name -> absolute sample path.

    A voice is any ``*.mp3`` / ``*.wav`` in the voices directory that is not a
    generated output file (``output*.mp3``).
    """
    voices = {}
    if not os.path.isdir(config.VOICES_DIR):
        return voices
    for filename in sorted(os.listdir(config.VOICES_DIR)):
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in (".mp3", ".wav"):
            continue
        if stem.lower().startswith("output"):
            continue
        path = os.path.join(config.VOICES_DIR, filename)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            voices[stem.upper()] = path
    return voices


def resolve_voice(name: str):
    """Return the sample path for ``name`` (case-insensitive) or ``None``."""
    if not name:
        return None
    return available_voices().get(name.strip().upper())


def voice_names() -> list:
    """Return the sorted list of available voice names (uppercase)."""
    return sorted(available_voices().keys())
