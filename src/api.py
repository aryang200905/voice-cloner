from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os
from src.services import generate_and_merge_tts, upload_to_s3
from src.core import get_s3_client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Voice Cloner API")

# Ensure the local S3 bucket exists
try:
    s3 = get_s3_client()
    s3.create_bucket(Bucket='my-local-bucket')
except Exception:
    pass

class TextInput(BaseModel):
    text: str
    name: str
    language: str

@app.get('/')
async def root():
    return {"message": "Voice Cloner API is running."}

@app.post('/generate_tts')
def generate_tts(item: TextInput):
    text = item.text
    name = item.name.upper()
    language = item.language.upper()
    
    list_of_names = ["SHUBHAM", "SUDHIR", "GARV"]
    list_of_languages = ["ENGLISH", "HINDI"]

    if not text.strip() or not name.strip() or not language.strip():
        return {"Error:" : "One or more requirements not provided"}
    if name not in list_of_names:
        return {"Error:" : "Name not available in the database"}
    if language not in list_of_languages:
        return {"Error:" : "Language not available to be cloned"}
    
    if name == "SHUBHAM":
        audio = os.path.join(BASE_DIR, "voices", "shubham.mp3")
    elif name == "SUDHIR":
        audio = os.path.join(BASE_DIR, "voices", "sudhir.mp3")
    else:
        audio = os.path.join(BASE_DIR, "voices", "garv.mp3")

    # Map language
    lang_code = "en" if language == "ENGLISH" else "hi"
    
    try:
        merged_output_path = generate_and_merge_tts(text, audio, lang_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    bucket_name = 'my-local-bucket'
    object_name = f'output_{uuid.uuid4().hex}.mp3'

    try:
        file_url = upload_to_s3(merged_output_path, bucket_name, object_name)
        return {"message": "Audio generated and uploaded to S3", "file_url": file_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading to S3: {str(e)}")
