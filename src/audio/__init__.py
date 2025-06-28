"""Audio package for EdutainmentForge."""

from .tts import TTSService, TTSError, create_tts_service
from .multivoice_tts import MultiVoiceTTSService, create_multivoice_tts_service

__all__ = [
    'TTSService', 
    'TTSError', 
    'create_tts_service',
    'MultiVoiceTTSService',
    'create_multivoice_tts_service'
]
