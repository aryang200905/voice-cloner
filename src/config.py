"""Environment-driven service settings."""
import os

# Project root (one level up from src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory holding the speaker reference samples.
VOICES_DIR = os.environ.get("VOICES_DIR", os.path.join(BASE_DIR, "voices"))

# --- TTS model ---
TTS_MODEL_NAME = os.environ.get(
    "TTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2"
)

# --- MongoDB ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "voiceCloning")
MONGO_INPUTS_COLLECTION = os.environ.get("MONGO_INPUTS_COLLECTION", "inputs")
MONGO_PROJECTS_COLLECTION = os.environ.get("MONGO_PROJECTS_COLLECTION", "projects")
WORKER_POLL_INTERVAL = float(os.environ.get("WORKER_POLL_INTERVAL", "15"))
MAX_TEXT_LENGTH = int(os.environ.get("MAX_TEXT_LENGTH", "5000"))

# --- S3 / LocalStack ---
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:4566")
S3_BUCKET = os.environ.get("S3_BUCKET", "my-local-bucket")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "dummy")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "dummy")
PRESIGNED_URL_EXPIRY = int(os.environ.get("PRESIGNED_URL_EXPIRY", "3600"))

# --- Supported languages ---
# Maps the human-facing name to the XTTS language code.
SUPPORTED_LANGUAGES = {
    "ENGLISH": "en",
    "HINDI": "hi",
}
