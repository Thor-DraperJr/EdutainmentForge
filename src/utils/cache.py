import os
from typing import Optional
from pydub import AudioSegment

CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", "./cache")

def get_cached_audio(cache_key: str) -> Optional[AudioSegment]:
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.mp3")
    if os.path.exists(cache_path):
        return AudioSegment.from_mp3(cache_path)
    return None

def cache_audio(cache_key: str, audio: AudioSegment):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.mp3")
    audio.export(cache_path, format="mp3")
