from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from dotenv import load_dotenv

import aiofiles
import aiofiles.os
import os
import time

from utils import SUPPORTED_LANGS

load_dotenv()

DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

async def voice_to_text(audio_file_path: str, lang: str) -> str:
    """Converts voice to text using Deepgram API"""
    
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f'Unsupported language: {lang}')
    
    deepgram = DeepgramClient()
    options = PrerecordedOptions(model="nova-2", smart_format=True, language=lang)
    
    async with aiofiles.open(audio_file_path, 'rb') as audio_file:
        
        buffer_data = await audio_file.read()
        payload: FileSource = {
            'buffer': buffer_data,
        }
        
        file_response = await deepgram.listen.asyncprerecorded.v("1").transcribe_file(payload, options)
        
    # save the response to json file
    output_dir = 'deepgram_responses'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, f'{time.time()}.json'), 'w') as f:
        f.write(file_response.to_json())
    
    return file_response.to_dict()['results']['channels'][0]['alternatives'][0]['transcript']
    

async def clean_audio_file(file_path: str) -> None:
    """Deletes audio file"""
    await aiofiles.os.remove(file_path)