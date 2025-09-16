"""
Audio processing compatibility layer for Python 3.13.

Provides fallback implementations when pydub/audioop are not available.
"""

import os
import wave
import tempfile
from pathlib import Path
from typing import List, Optional
import struct

from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import pydub, fallback to basic audio processing if not available
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    logger.info("pydub available - using advanced audio processing")
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - using basic audio processing")


class AudioProcessor:
    """Audio processing with fallback for systems without pydub."""
    
    def __init__(self):
        self.use_pydub = PYDUB_AVAILABLE
    
    def combine_wav_files(self, input_files: List[Path], output_file: Path, 
                         pause_duration_ms: int = 300) -> bool:
        """
        Combine multiple WAV files into one, with optional pauses.
        
        Args:
            input_files: List of input WAV file paths
            output_file: Output file path
            pause_duration_ms: Pause between files in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_pydub:
                return self._combine_with_pydub(input_files, output_file, pause_duration_ms)
            else:
                return self._combine_with_wave(input_files, output_file, pause_duration_ms)
        except Exception as e:
            logger.error(f"Failed to combine audio files: {e}")
            return False
    
    def _combine_with_pydub(self, input_files: List[Path], output_file: Path, 
                           pause_duration_ms: int) -> bool:
        """Combine using pydub (when available)."""
        audio_segments = []
        
        for i, file_path in enumerate(input_files):
            if file_path.exists():
                audio_segment = AudioSegment.from_wav(str(file_path))
                audio_segments.append(audio_segment)
                
                # Add pause between segments (except after the last one)
                if i < len(input_files) - 1 and pause_duration_ms > 0:
                    pause = AudioSegment.silent(duration=pause_duration_ms)
                    audio_segments.append(pause)
        
        if audio_segments:
            combined_audio = sum(audio_segments)
            combined_audio.export(str(output_file), format="wav")
            return True
        
        return False
    
    def _combine_with_wave(self, input_files: List[Path], output_file: Path, 
                          pause_duration_ms: int) -> bool:
        """Combine using basic wave module (fallback)."""
        if not input_files:
            return False
        
        # Read the first file to get audio parameters
        first_file = input_files[0]
        if not first_file.exists():
            logger.error(f"First input file does not exist: {first_file}")
            return False
        
        with wave.open(str(first_file), 'rb') as first_wave:
            params = first_wave.getparams()
            sample_rate = params.framerate
            channels = params.nchannels
            sample_width = params.sampwidth
        
        # Calculate pause samples
        pause_frames = 0
        if pause_duration_ms > 0:
            pause_frames = int(sample_rate * pause_duration_ms / 1000.0)
        
        # Open output file
        with wave.open(str(output_file), 'wb') as output_wave:
            output_wave.setparams(params)
            
            for i, file_path in enumerate(input_files):
                if not file_path.exists():
                    logger.warning(f"Input file does not exist: {file_path}")
                    continue
                
                # Copy audio data from input file
                with wave.open(str(file_path), 'rb') as input_wave:
                    frames = input_wave.readframes(input_wave.getnframes())
                    output_wave.writeframes(frames)
                
                # Add pause between files (except after the last one)
                if i < len(input_files) - 1 and pause_frames > 0:
                    # Create silent frames (zeros)
                    silence = b'\x00' * (pause_frames * channels * sample_width)
                    output_wave.writeframes(silence)
        
        logger.info(f"Successfully combined {len(input_files)} audio files using wave module")
        return True
    
    def create_silent_audio(self, duration_ms: int, sample_rate: int = 22050, 
                           channels: int = 1) -> Optional[Path]:
        """
        Create a silent audio file.
        
        Args:
            duration_ms: Duration in milliseconds
            sample_rate: Sample rate (default 22050)
            channels: Number of channels (default 1)
            
        Returns:
            Path to the created file, or None if failed
        """
        try:
            temp_file = Path(tempfile.mktemp(suffix='.wav'))
            
            frames = int(sample_rate * duration_ms / 1000.0)
            sample_width = 2  # 16-bit
            
            with wave.open(str(temp_file), 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                
                # Write silent frames
                silence = b'\x00' * (frames * channels * sample_width)
                wav_file.writeframes(silence)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"Failed to create silent audio: {e}")
            return None


# Global instance
_audio_processor = None

def get_audio_processor() -> AudioProcessor:
    """Get the global audio processor instance."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor