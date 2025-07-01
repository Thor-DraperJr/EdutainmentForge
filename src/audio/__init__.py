"""Audio package for EdutainmentForge."""

from .tts import TTSService, TTSError, create_tts_service
from .multivoice_tts import MultiVoiceTTSService, create_multivoice_tts_service

# Import premium integration for smart service selection
from utils.premium_integration import get_best_multivoice_tts_service

def create_best_multivoice_tts_service(config):
    """Create the best available multi-voice TTS service (premium or standard)."""
    return get_best_multivoice_tts_service(config)

__all__ = [
    'TTSService', 
    'TTSError', 
    'create_tts_service',
    'MultiVoiceTTSService',
    'create_multivoice_tts_service',
    'create_best_multivoice_tts_service'
]
