"""Shared model and S3 clients."""

from functools import lru_cache
from threading import Lock

import boto3

from src import config


# XTTS inference uses a shared model instance. Serialize access to it across
# FastAPI's thread pool and any other threads in this process.
tts_lock = Lock()


@lru_cache(maxsize=1)
def get_tts_model():
    """Load the model on first use, once per process."""
    import torch
    from TTS.api import TTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return TTS(config.TTS_MODEL_NAME).to(device)


def get_s3_client():
    """Return a client for the configured S3 service."""
    kwargs = {"region_name": config.S3_REGION}
    if config.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.S3_ENDPOINT_URL
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    return boto3.client("s3", **kwargs)
