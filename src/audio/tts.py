"""
Text-to-Speech service integration.

Handles converting text scripts to speech audio using various TTS services.
"""

import os
import io
import sys
from pathlib import Path
from typing import Dict, Optional, BinaryIO
from abc import ABC, abstractmethod

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
    print("✓ Azure Speech SDK loaded successfully")
except ImportError as e:
    AZURE_AVAILABLE = False
    print(f"⚠ Azure Speech SDK not available: {e}")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from utils.logger import get_logger


logger = get_logger(__name__)


class TTSError(Exception):
    """Raised when text-to-speech conversion fails."""
    pass


class TTSService(ABC):
    """Abstract base class for text-to-speech services."""
    
    @abstractmethod
    def synthesize_text(self, text: str, output_path: Path) -> bool:
        """
        Convert text to speech and save to file.
        
        Args:
            text: Text content to convert
            output_path: Path where audio file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voices for this TTS service."""
        pass


class AzureTTSService(TTSService):
    """Azure Cognitive Services Text-to-Speech implementation."""
    
    def __init__(self, api_key: str, region: str, voice: str = "en-US-AriaNeural"):
        """
        Initialize Azure TTS service.
        
        Args:
            api_key: Azure Speech Services API key
            region: Azure region (e.g., 'eastus')
            voice: Voice name to use for synthesis
        """
        if not AZURE_AVAILABLE:
            raise TTSError("Azure Speech SDK not available. Install with: pip install azure-cognitiveservices-speech")
        
        self.api_key = api_key
        self.region = region
        self.voice = voice
        
        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region
        )
        self.speech_config.speech_synthesis_voice_name = voice
        
        logger.info(f"Initialized Azure TTS with voice: {voice}")
    
    def synthesize_text(self, text: str, output_path: Path) -> bool:
        """Convert text to speech using Azure TTS."""
        try:
            logger.info(f"Synthesizing text to {output_path}")
            
            # Configure audio output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Perform synthesis
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Successfully synthesized audio: {output_path}")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation.reason}")
                if cancellation.error_details:
                    logger.error(f"Error details: {cancellation.error_details}")
                return False
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Azure TTS synthesis failed: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available Azure voices."""
        # Common Azure neural voices
        return {
            "en-US-AriaNeural": "Aria (US English, Female)",
            "en-US-GuyNeural": "Guy (US English, Male)",
            "en-US-JennyNeural": "Jenny (US English, Female)",
            "en-US-DavisNeural": "Davis (US English, Male)",
            "en-GB-LibbyNeural": "Libby (UK English, Female)",
            "en-GB-RyanNeural": "Ryan (UK English, Male)",
        }


class LocalTTSService(TTSService):
    """Local text-to-speech using pyttsx3."""
    
    def __init__(self, voice_id: Optional[str] = None, rate: int = 150, volume: float = 0.9):
        """
        Initialize local TTS service.
        
        Args:
            voice_id: System voice ID to use
            rate: Speaking rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        if not PYTTSX3_AVAILABLE:
            raise TTSError("pyttsx3 not available. Install with: pip install pyttsx3")
        
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        
        # Initialize engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        if voice_id:
            self.engine.setProperty('voice', voice_id)
        
        logger.info("Initialized local TTS service")
    
    def synthesize_text(self, text: str, output_path: Path) -> bool:
        """Convert text to speech using local TTS."""
        try:
            logger.info(f"Synthesizing text to {output_path}")
            
            # Save to file
            self.engine.save_to_file(text, str(output_path))
            self.engine.runAndWait()
            
            # Check if file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully synthesized audio: {output_path}")
                return True
            else:
                logger.error("Local TTS failed to create audio file")
                return False
                
        except Exception as e:
            logger.error(f"Local TTS synthesis failed: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available system voices."""
        try:
            voices = self.engine.getProperty('voices')
            return {voice.id: voice.name for voice in voices if voice}
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return {}


def create_tts_service(config: Dict) -> TTSService:
    """
    Create TTS service based on configuration.
    
    Args:
        config: Application configuration dictionary
        
    Returns:
        Configured TTS service instance
        
    Raises:
        TTSError: If no suitable TTS service can be created
    """
    tts_service = config.get('tts_service', 'azure').lower()
    
    if tts_service == 'azure' and config.get('tts_api_key'):
        if not AZURE_AVAILABLE:
            logger.warning("Azure TTS requested but SDK not available, falling back to local TTS")
        else:
            try:
                return AzureTTSService(
                    api_key=config['tts_api_key'],
                    region=config.get('tts_region', 'eastus'),
                    voice=config.get('tts_voice', 'en-US-AriaNeural')
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Azure TTS: {e}, falling back to local TTS")
    
    # Fall back to local TTS
    if PYTTSX3_AVAILABLE:
        return LocalTTSService()
    
    raise TTSError("No TTS service available. Install either azure-cognitiveservices-speech or pyttsx3")


def create_sample_audio(output_path: Path) -> bool:
    """
    Create a sample audio file for testing without TTS services.
    
    Args:
        output_path: Path where sample audio should be saved
        
    Returns:
        True if sample was created successfully
    """
    try:
        # Create a simple text file as placeholder
        sample_text = "This is a sample audio file for EdutainmentForge testing."
        
        # Write as text file with .txt extension for now
        text_path = output_path.with_suffix('.txt')
        text_path.write_text(sample_text)
        
        logger.info(f"Created sample text file: {text_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample audio: {e}")
        return False
