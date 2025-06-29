import hashlib
import os
from typing import Optional
from pydub import AudioSegment
from utils.cache import get_cached_audio, cache_audio
from utils.logger import logger


class SpeechGenerationError(Exception):
    """Custom exception for speech generation failures."""
    pass


def call_tts_service(ssml_text: str, voice: str) -> AudioSegment:
    """
    Call the TTS service to generate audio from SSML text.
    
    Args:
        ssml_text: SSML formatted text
        voice: Voice identifier
        
    Returns:
        AudioSegment object containing generated speech
        
    Raises:
        Exception: If TTS service fails
    """
    # This is a placeholder - in a real implementation, this would
    # call Azure Cognitive Services or another TTS service
    # For now, return a mock AudioSegment
    from pydub.generators import Sine
    return Sine(440).to_audio_segment(duration=1000)


def generate_speech(ssml_text: str, voice: str) -> AudioSegment:
    """
    Generate speech audio from SSML text, using caching to optimize performance.

    Args:
        ssml_text: SSML formatted text.
        voice: Voice identifier.

    Returns:
        AudioSegment object containing generated speech.
    """
    cache_key = hashlib.sha256(f"{voice}_{ssml_text}".encode()).hexdigest()
    cached_audio: Optional[AudioSegment] = get_cached_audio(cache_key)
    if cached_audio:
        logger.info(f"Cache hit for key: {cache_key}")
        return cached_audio

    try:
        audio = call_tts_service(ssml_text, voice)
        cache_audio(cache_key, audio)
        logger.info(f"Generated and cached audio for key: {cache_key}")
        return audio
    except Exception as e:
        logger.error(f"Speech generation failed: {e}")
        raise SpeechGenerationError(f"Speech generation failed: {e}")