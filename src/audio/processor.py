"""
Audio processing and enhancement utilities.

Handles audio file manipulation, mixing, and post-processing.
"""

import os
from pathlib import Path
from typing import Optional, List

try:
    from pydub import AudioSegment
    from pydub.effects import normalize
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    # Create dummy class for type hints when pydub not available
    class AudioSegment:
        pass

from utils.logger import get_logger


logger = get_logger(__name__)


class AudioProcessingError(Exception):
    """Raised when audio processing fails."""
    pass


class AudioProcessor:
    """Handles audio file processing and enhancement."""
    
    def __init__(self):
        """Initialize audio processor."""
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available. Audio processing features limited.")
        
        self.supported_formats = ['mp3', 'wav', 'ogg', 'flv', 'mp4']
    
    def process_audio(
        self,
        input_path: Path,
        output_path: Path,
        normalize_audio: bool = True,
        add_intro: bool = False,
        add_outro: bool = False,
        background_music_path: Optional[Path] = None
    ) -> bool:
        """
        Process and enhance audio file.
        
        Args:
            input_path: Path to input audio file
            output_path: Path for output audio file
            normalize_audio: Whether to normalize audio levels
            add_intro: Whether to add intro music/sound
            add_outro: Whether to add outro music/sound
            background_music_path: Optional background music file
            
        Returns:
            True if processing successful
        """
        if not PYDUB_AVAILABLE:
            logger.warning("Audio processing skipped - pydub not available")
            # Just copy file if no processing available
            try:
                import shutil
                shutil.copy2(input_path, output_path)
                return True
            except Exception as e:
                logger.error(f"Failed to copy audio file: {e}")
                return False
        
        try:
            logger.info(f"Processing audio: {input_path} -> {output_path}")
            
            # Load main audio
            audio = AudioSegment.from_file(str(input_path))
            
            # Normalize audio levels
            if normalize_audio:
                audio = normalize(audio)
                logger.debug("Applied audio normalization")
            
            # Add intro if requested
            if add_intro:
                intro = self._create_intro_audio()
                if intro:
                    audio = intro + audio
                    logger.debug("Added intro audio")
            
            # Add outro if requested
            if add_outro:
                outro = self._create_outro_audio()
                if outro:
                    audio = audio + outro
                    logger.debug("Added outro audio")
            
            # Add background music if provided
            if background_music_path and background_music_path.exists():
                audio = self._add_background_music(audio, background_music_path)
                logger.debug("Added background music")
            
            # Export processed audio
            audio.export(str(output_path), format=output_path.suffix[1:])
            logger.info(f"Successfully processed audio: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return False
    
    def _create_intro_audio(self) -> Optional[AudioSegment]:
        """Create intro audio segment."""
        try:
            # Create a simple tone or use pre-recorded intro
            # For now, create silence as placeholder
            intro = AudioSegment.silent(duration=1000)  # 1 second silence
            return intro
        except Exception as e:
            logger.error(f"Failed to create intro audio: {e}")
            return None
    
    def _create_outro_audio(self) -> Optional[AudioSegment]:
        """Create outro audio segment."""
        try:
            # Create a simple tone or use pre-recorded outro
            # For now, create silence as placeholder
            outro = AudioSegment.silent(duration=1000)  # 1 second silence
            return outro
        except Exception as e:
            logger.error(f"Failed to create outro audio: {e}")
            return None
    
    def _add_background_music(
        self,
        main_audio: AudioSegment,
        music_path: Path,
        volume_reduction: int = 20
    ) -> AudioSegment:
        """
        Add background music to main audio.
        
        Args:
            main_audio: Main audio track
            music_path: Path to background music file
            volume_reduction: DB reduction for background music
            
        Returns:
            Mixed audio segment
        """
        try:
            # Load background music
            background = AudioSegment.from_file(str(music_path))
            
            # Reduce background music volume
            background = background - volume_reduction
            
            # Loop background music if needed
            if len(background) < len(main_audio):
                loops_needed = (len(main_audio) // len(background)) + 1
                background = background * loops_needed
            
            # Trim background to match main audio length
            background = background[:len(main_audio)]
            
            # Mix the audio tracks
            mixed = main_audio.overlay(background)
            
            return mixed
            
        except Exception as e:
            logger.error(f"Failed to add background music: {e}")
            return main_audio
    
    def get_audio_info(self, audio_path: Path) -> dict:
        """
        Get information about an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        if not PYDUB_AVAILABLE:
            # Basic file info without pydub
            try:
                stat = audio_path.stat()
                return {
                    'file_size': stat.st_size,
                    'format': audio_path.suffix[1:],
                    'duration': 'unknown',
                    'channels': 'unknown',
                    'sample_rate': 'unknown'
                }
            except Exception:
                return {}
        
        try:
            audio = AudioSegment.from_file(str(audio_path))
            return {
                'duration': len(audio) / 1000.0,  # Convert to seconds
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'format': audio_path.suffix[1:],
                'file_size': audio_path.stat().st_size
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {}
    
    def convert_format(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert audio file to different format.
        
        Args:
            input_path: Source audio file
            output_path: Target audio file with desired format
            
        Returns:
            True if conversion successful
        """
        if not PYDUB_AVAILABLE:
            logger.error("Audio format conversion requires pydub")
            return False
        
        try:
            logger.info(f"Converting {input_path} to {output_path}")
            
            audio = AudioSegment.from_file(str(input_path))
            audio.export(str(output_path), format=output_path.suffix[1:])
            
            logger.info(f"Successfully converted to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False
