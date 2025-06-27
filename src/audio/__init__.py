"""Audio package for EdutainmentForge."""

from .tts import TTSService, TTSError, create_tts_service, create_sample_audio
from .processor import AudioProcessor, AudioProcessingError

__all__ = ['TTSService', 'TTSError', 'create_tts_service', 'create_sample_audio', 
           'AudioProcessor', 'AudioProcessingError']
