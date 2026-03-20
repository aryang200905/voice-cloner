import torch
import boto3
from TTS.api import TTS
from pydub import AudioSegment
from pydub.utils import which

# Configure pydub to use standard ffmpeg
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# Initialize TTS model globally to avoid reloading on every request
device = "cuda" if torch.cuda.is_available() else "cpu"
tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def get_s3_client():
    """Returns a configured boto3 S3 client pointing to LocalStack."""
    return boto3.client(
        's3',
        endpoint_url='http://localhost:4566',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
