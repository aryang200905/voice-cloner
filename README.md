# Voice Cloner API

This project provides a Voice Cloning service utilizing `TTS` (Coqui-AI), FastAPI, and MongoDB. It allows users to clone specific voices and generate text-to-speech audio outputs that are stored in local S3 (via LocalStack) and managed through a MongoDB database.

## Features
- **Voice Cloning Generation:** Generate accurate text-to-speech in English and Hindi.
- **REST API:** A FastAPI service for interacting directly with the TTS models.
- **MongoDB Worker:** A polling worker that processes asynchronous jobs stored in a MongoDB collection.
- **S3 Integration:** Uploads generated `.mp3` files to an S3-compatible service (LocalStack default) and generates pre-signed download URLs.

## Project Structure
- `src/api.py`: The FastAPI application exposing the `/generate_tts` endpoint.
- `src/worker.py`: A MongoDB polling script that processes audio generation requests in the background.
- `src/create_bucket.py`: A utility script to initialize a local S3 bucket.
- `voices/`: Directory containing voice sample `.mp3` files (e.g., `garv.mp3`, `sudhir.mp3`, etc.).
- `examples/`: Sample FastAPI applications for testing purposes.

## Requirements
To install the dependencies, you can use:
```sh
pip install fastapi[all] uvicorn pymongo boto3 pydub torch TTS
```
*Note: Depending on your hardware (CPU vs CUDA), please consult the official PyTorch installation guide.*

## Usage
### Running the FastAPI Service
```sh
uvicorn src.api:app --reload
```
You can access the API documentation at `http://localhost:8000/docs`.

### Running the MongoDB Worker
To start polling the database and generating audio sequentially:
```sh
python src/worker.py
```

### Local S3 Setup
If you do not have an actual AWS S3 bucket, it is configured to use LocalStack. Ensure LocalStack is running and execute:
```sh
python src/create_bucket.py
```
