"""
Multi-voice TTS service for podcast generation with multiple speakers.

Handles parsing dialogue scripts and using different voices for different speakers.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from pydub import AudioSegment
import tempfile

from .tts import AzureTTSService, TTSError
from utils.logger import get_logger

logger = get_logger(__name__)


class MultiVoiceTTSService:
    """TTS service that handles multiple speakers with different voices."""
    
    def __init__(self, config: Dict):
        """
        Initialize multi-voice TTS service.
        
        Args:
            config: Configuration dictionary with API keys and voice mappings
        """
        self.api_key = config.get('tts_api_key')
        self.region = config.get('tts_region', 'eastus2')
        
        if not self.api_key:
            raise TTSError("TTS API key is required")
        
        # Define voice mappings for each speaker - now with S0 tier premium features
        use_premium_voices = config.get('use_premium_voices', os.getenv('USE_PREMIUM_VOICES', 'true').lower() == 'true')
        
        if use_premium_voices:
            # Premium neural voices optimized for podcast content with natural speech patterns
            self.speaker_voices = {
                'Sarah': config.get('sarah_voice', 'en-US-EmmaNeural'),     # Premium female voice, natural and conversational
                'Mike': config.get('mike_voice', 'en-US-DavisNeural'),     # Premium male voice, conversational 
                'Narrator': config.get('narrator_voice', 'en-US-EmmaNeural') # Premium female voice, clear and professional
            }
            # Enable premium voice styles and emotional range
            self.voice_styles = {
                'Sarah': 'cheerful',         # Engaging, enthusiastic style for learning content
                'Mike': 'friendly',          # Warm, approachable tone for explanations
                'Narrator': 'newscast'       # Clear, professional delivery for important points
            }
            logger.info("🎤 Using premium S0 neural voices with enhanced styles")
        else:
            # Basic neural voices without premium styling
            self.speaker_voices = {
                'Sarah': config.get('sarah_voice', 'en-US-AriaNeural'),     # Basic female voice
                'Mike': config.get('mike_voice', 'en-US-DavisNeural'),      # Basic male voice
                'Narrator': config.get('narrator_voice', 'en-US-JennyNeural')  # Basic neutral voice
            }
            self.voice_styles = {}  # No premium styles on basic tier
        
        # Cache TTS service instances to avoid recreation
        self._tts_cache = {}
        
        logger.info(f"Initialized multi-voice TTS with voices: {self.speaker_voices}")
        logger.info(f"Using API key ending in: ...{self.api_key[-4:] if self.api_key else 'None'}")
        logger.info(f"Using region: {self.region}")
    
    def synthesize_dialogue_script(self, script: str, output_path: Path, progress_callback=None) -> bool:
        """
        Convert a dialogue script to audio with multiple voices.
        
        Args:
            script: Script text with speaker labels (e.g., "Sarah: Hello everyone!")
            output_path: Path where final audio should be saved
            progress_callback: Optional callback function to report progress (progress_percent, message)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse script into dialogue segments
            dialogue_segments = self._parse_dialogue_script(script)
            
            if not dialogue_segments:
                logger.error("No dialogue segments found in script")
                return False

            if progress_callback:
                try:
                    progress_callback(72, f"Generating {len(dialogue_segments)} audio segments...")
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

            # Generate audio for each segment
            audio_segments = []
            temp_dir = Path(tempfile.mkdtemp())
            
            for i, (speaker, text) in enumerate(dialogue_segments):
                # Update progress for each segment (with error handling)
                try:
                    if progress_callback:
                        segment_progress = 72 + (20 * i / len(dialogue_segments))  # 72-92% for TTS generation
                        progress_callback(int(segment_progress), f"Generating audio for {speaker} ({i+1}/{len(dialogue_segments)})...")
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
                
                temp_file = temp_dir / f"segment_{i:03d}.wav"
                
                # Get voice for this speaker
                voice = self.speaker_voices.get(speaker, self.speaker_voices['Narrator'])
                
                # Get or create TTS service for this voice (cached)
                if voice not in self._tts_cache:
                    # Get voice style for premium features
                    voice_style = self.voice_styles.get(speaker) if hasattr(self, 'voice_styles') else None
                    
                    self._tts_cache[voice] = AzureTTSService(
                        api_key=self.api_key,
                        region=self.region,
                        voice=voice,
                        voice_style=voice_style
                    )
                
                tts_service = self._tts_cache[voice]
                
                logger.info(f"Generating audio for {speaker} with voice {voice}")
                
                # Synthesize this segment
                success = tts_service.synthesize_text(text, temp_file)
                if not success:
                    logger.error(f"Failed to synthesize segment for {speaker}")
                    return False
                
                # Load the audio segment
                if temp_file.exists():
                    audio_segment = AudioSegment.from_wav(str(temp_file))
                    audio_segments.append(audio_segment)
                    
                    # Add a small pause between speakers (300ms)
                    if i < len(dialogue_segments) - 1:
                        pause = AudioSegment.silent(duration=300)
                        audio_segments.append(pause)
                else:
                    logger.error(f"Audio file not created for segment {i}")
                    return False
            
            # Combine all audio segments
            if progress_callback:
                try:
                    progress_callback(92, "Assembling audio segments...")
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
                
            if audio_segments:
                combined_audio = sum(audio_segments)
                
                if progress_callback:
                    try:
                        progress_callback(96, "Finalizing audio file...")
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
                
                # Export the final audio
                combined_audio.export(str(output_path), format="wav")
                logger.info(f"Successfully created multi-voice podcast: {output_path}")
                
                if progress_callback:
                    try:
                        progress_callback(98, "Cleaning up temporary files...")
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
                
                # Cleanup temp files
                for temp_file in temp_dir.glob("*.wav"):
                    temp_file.unlink()
                temp_dir.rmdir()
                
                return True
            else:
                logger.error("No audio segments to combine")
                return False
                
        except Exception as e:
            logger.error(f"Multi-voice synthesis failed: {e}")
            return False
    
    def _parse_dialogue_script(self, script: str) -> List[Tuple[str, str]]:
        """
        Parse script into dialogue segments with speaker identification.
        
        Args:
            script: Full script text
            
        Returns:
            List of (speaker, text) tuples
        """
        segments = []
        
        # Split script into lines and process each
        lines = script.split('\n')
        current_speaker = 'Narrator'
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a speaker name followed by colon
            speaker_match = re.match(r'^(Sarah|Mike|Narrator):\s*(.+)', line)
            
            if speaker_match:
                # Save previous segment if exists
                if current_text:
                    combined_text = ' '.join(current_text).strip()
                    if combined_text:
                        segments.append((current_speaker, combined_text))
                
                # Start new segment
                current_speaker = speaker_match.group(1)
                current_text = [speaker_match.group(2)]
            else:
                # Continue current speaker's text
                current_text.append(line)
        
        # Add final segment
        if current_text:
            combined_text = ' '.join(current_text).strip()
            if combined_text:
                segments.append((current_speaker, combined_text))
        
        logger.info(f"Parsed script into {len(segments)} dialogue segments")
        return segments
    
    def get_speaker_voices(self) -> Dict[str, str]:
        """Get current voice mappings for speakers."""
        return self.speaker_voices.copy()
    
    def update_speaker_voice(self, speaker: str, voice: str):
        """Update voice for a specific speaker."""
        if speaker in self.speaker_voices:
            self.speaker_voices[speaker] = voice
            logger.info(f"Updated {speaker}'s voice to {voice}")
        else:
            logger.warning(f"Unknown speaker: {speaker}")


def create_multivoice_tts_service(config: Dict) -> MultiVoiceTTSService:
    """
    Factory function to create multi-voice TTS service.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured MultiVoiceTTSService instance
    """
    return MultiVoiceTTSService(config)
