# Voice Cloner API

Generate English or Hindi speech with a reference voice using Coqui XTTS v2. The FastAPI endpoint generates audio immediately; a separate MongoDB worker handles queued jobs. Both upload MP3 output to an S3-compatible bucket and return a download URL that expires after one hour by default.

## Setup

Use a Python environment supported by your Coqui TTS installation. Install `ffmpeg` and `ffprobe` on the system path, then install the Python dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Coqui's XTTS model must be downloaded on first use. Review and accept its model license using Coqui's normal setup process before running the service unattended. The service does not accept the license for you.

By default, storage points at LocalStack on `http://localhost:4566`. Start LocalStack with S3 enabled, create the bucket, and start the API from the repository root:

```sh
python -m src.create_bucket
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

The API docs are at `http://127.0.0.1:8000/docs`. `GET /voices` lists usable reference files and languages. `POST /generate_tts` accepts JSON such as:

```json
{"text": "Hello, how are you?", "name": "garv", "language": "English"}
```

Voice names come from nonempty `.mp3` or `.wav` files in `voices/`, excluding files named `output*`. The included reference names are `garv`, `sameer`, `sanjay`, `sanjeev`, and `sudhir`. Add a properly licensed voice sample there to make another name available. Clear, clean speech in the target voice makes a better reference than noisy or mixed audio. Keep any voice data and output in accordance with consent and applicable rights.

## Queue worker

Start MongoDB, then run:

```sh
python -m src.worker
```

The worker reads the `voiceCloning.inputs` collection by default. A request needs `user_id` (positive integer), `text`, `voice_id`, and `language` (`English` or `Hindi`). It claims records with missing, null, `"0"`, or `"pending"` status and processes the lowest `id` first. Its status values are `"1"` (claimed), `"2"` (generating), `"3"` (uploading), `"4"` (complete), and `"failed"`. Completed jobs keep `audio_link`; failed jobs keep `error`. To retry a failed or interrupted job, set its status back to `"pending"` after checking whether the previous run uploaded an object. On success, the worker also writes `audio_link` and increments `edit_flag` in the matching `projects` record.

## Configuration

Set environment variables before starting the process. See [.env.example](.env.example) for defaults. The file is a reference; it is not loaded automatically. Set `S3_ENDPOINT_URL` to an empty string to use the normal AWS endpoint and credentials from the AWS credential chain. Generated audio uses per-request temporary files and removes them after upload.

## Tests

```sh
python -m unittest discover -s tests
```

The lightweight tests do not download the model or require MongoDB or S3. A full end-to-end run requires those services, the Python dependencies, the model, and a working `ffmpeg` installation.
