import textwrap
import os
import uuid
from pydub import AudioSegment
from src.core import tts_model, get_s3_client

def split_text(text, max_length=400):
    """Splits text into chunks of maximum length suitable for the TTS model."""
    return textwrap.wrap(text, max_length)

def generate_and_merge_tts(text: str, audio_speaker_path: str, language: str) -> str:
    """
    Generates TTS audio chunks and merges them into a single audio file.
    Always uses 'output.mp3' as the temporary output file.
    Returns the path to the merged file.
    """
    output_files = []
    try:
        for idx, chunk in enumerate(split_text(text)):
            output_file_path = f"output_{idx}_{uuid.uuid4().hex}.mp3"
            tts_model.tts_to_file(
                text=chunk,
                speaker_wav=audio_speaker_path,
                language=language,
                file_path=output_file_path
            )
            output_files.append(output_file_path)
    except Exception as e:
        raise Exception(f"Error generating audio: {str(e)}")
    
    # Merge the generated audio chunks
    merged = AudioSegment.empty()
    for output_file_path in output_files:
        audio_segment = AudioSegment.from_file(output_file_path)
        merged += audio_segment
        # Clean up chunk
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
    
    merged_output_path = "output.mp3"
    merged.export(merged_output_path, format="mp3")
    return merged_output_path

def upload_to_s3(file_path: str, bucket_name: str, object_name: str) -> str:
    """
    Uploads a file to the specified S3 bucket and returns a presigned URL.
    """
    s3 = get_s3_client()
    s3.upload_file(file_path, bucket_name, object_name)
    file_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_name},
        ExpiresIn=3600
    )
    return file_url
