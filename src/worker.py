import time
import uuid
from pymongo import MongoClient
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.services import generate_and_merge_tts, upload_to_s3
from src.core import get_s3_client

# Ensure the local S3 bucket exists
try:
    s3 = get_s3_client()
    s3.create_bucket(Bucket='my-local-bucket')
except Exception:
    pass

def generate_audio(audios_collection, projects_collection):
    print("Worker started: Polling MongoDB for audio generation requests...")
    while True:
        document = audios_collection.find_one({}, sort=[('id', 1)])
        if document:
            audios_collection.update_one({"_id": document['_id']}, {"$set": {"status": "1"}})
            
            try:
                audio_id = int(document.get('user_id', 0))
            except (ValueError, TypeError):
                audio_id = 0
                
            language = document.get('language') or ''
            language = str(language).upper()
            
            text = document.get('text') or ''
            text = str(text)
            
            name = document.get('voice_id') or ''
            name = str(name).lower()
            
            list_of_languages = ["ENGLISH", "HINDI"]
            
            # Validation
            if len(text.strip()) == 0 or audio_id <= 0 or len(language.strip()) == 0:
                document2 = projects_collection.find_one({'user_id': audio_id})
                if document2:
                    projects_collection.update_one({"_id": document2['_id']}, {"$set": {"audio_link": "Error: One or more requirements not provided"}})
                audios_collection.delete_one({'_id': document['_id']})
                continue
                
            if language not in list_of_languages:
                document2 = projects_collection.find_one({'user_id': audio_id})
                if document2:
                    projects_collection.update_one({"_id": document2['_id']}, {"$set": {"audio_link": "Error: Language not available to be cloned"}})
                audios_collection.delete_one({'_id': document['_id']})
                continue
                
            # Transition to generating state
            audios_collection.update_one({"_id": document['_id']}, {"$set": {"status": "2"}})
            
            # Determine params
            lang_code = "en" if language == "ENGLISH" else "hi"
            audio_path = os.path.join(BASE_DIR, "voices", f"{name}.mp3")
            
            try:
                # Generate, merge and upload
                merged_output_path = generate_and_merge_tts(text, audio_path, lang_code)
                audios_collection.update_one({"_id": document['_id']}, {"$set": {"status": "3"}})
                
                bucket_name = 'my-local-bucket'
                object_name = f'output_{uuid.uuid4().hex}.mp3'
                
                # Upload
                file_url = upload_to_s3(merged_output_path, bucket_name, object_name)
                
                # Update frontend collections
                document2 = projects_collection.find_one({'user_id': audio_id})
                if document2:
                    projects_collection.update_one({"_id": document2['_id']}, {"$set": {"audio_link": file_url}})
                    projects_collection.update_one({"_id": document2['_id']}, {"$set": {"edit_flag": document2.get('edit_flag', 0) + 1}})
                
                # Update final status
                audios_collection.update_one({"_id": document['_id']}, {"$set": {"status": "4"}})
            except Exception as e:
                print(f"Error processing audio request for {audio_id}: {e}")
                
            # Cleanup request
            audios_collection.delete_one({'_id': document['_id']})
        else:
            time.sleep(15)

if __name__ == "__main__":
    # Initialize MongoDB client and start the worker
    client = MongoClient('mongodb://127.0.0.1:27017/')
    db = client['voiceCloning']
    generate_audio(db['inputs'], db['projects'])
