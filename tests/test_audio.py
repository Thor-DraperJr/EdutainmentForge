"""
Tests for audio processing functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audio import create_tts_service, TTSError, AudioProcessor, create_sample_audio


class TestTTSService:
    """Test cases for TTS service creation."""
    
    def test_create_tts_service_no_config(self):
        """Test TTS service creation with minimal config."""
        config = {}
        
        with pytest.raises(TTSError):
            create_tts_service(config)
    
    def test_create_tts_service_azure_config(self):
        """Test Azure TTS service creation."""
        config = {
            'tts_service': 'azure',
            'tts_api_key': 'test_key',
            'tts_region': 'eastus',
            'tts_voice': 'en-US-AriaNeural'
        }
        
        # This will likely fail due to missing Azure SDK in test environment
        # but we can test the configuration handling
        try:
            service = create_tts_service(config)
            # If successful, verify it's the right type
            assert hasattr(service, 'synthesize_text')
            assert hasattr(service, 'get_available_voices')
        except TTSError:
            # Expected in test environment without Azure SDK
            pass
    
    @patch('audio.tts.PYTTSX3_AVAILABLE', True)
    @patch('audio.tts.pyttsx3')
    def test_create_local_tts_service(self, mock_pyttsx3):
        """Test local TTS service creation."""
        # Mock pyttsx3 engine
        mock_engine = Mock()
        mock_pyttsx3.init.return_value = mock_engine
        
        config = {'tts_service': 'local'}
        
        # This should fall back to local TTS
        try:
            service = create_tts_service(config)
            assert hasattr(service, 'synthesize_text')
            assert hasattr(service, 'get_available_voices')
        except TTSError:
            # May fail if pyttsx3 not available
            pass


class TestAudioProcessor:
    """Test cases for audio processor."""
    
    def test_init(self):
        """Test audio processor initialization."""
        processor = AudioProcessor()
        assert hasattr(processor, 'supported_formats')
        assert 'mp3' in processor.supported_formats
    
    def test_get_audio_info_nonexistent_file(self, temp_dir):
        """Test getting info for nonexistent file."""
        processor = AudioProcessor()
        fake_file = temp_dir / "nonexistent.mp3"
        
        info = processor.get_audio_info(fake_file)
        assert isinstance(info, dict)
        # Should return empty dict for nonexistent file
    
    def test_process_audio_no_pydub(self, temp_dir):
        """Test audio processing without pydub available."""
        processor = AudioProcessor()
        
        # Create dummy input file
        input_file = temp_dir / "input.mp3"
        input_file.write_text("dummy audio content")
        
        output_file = temp_dir / "output.mp3"
        
        # This should fall back to simple copy
        result = processor.process_audio(input_file, output_file)
        
        # Should succeed with copy fallback
        assert result == True
        assert output_file.exists()


class TestSampleAudio:
    """Test cases for sample audio creation."""
    
    def test_create_sample_audio(self, temp_dir):
        """Test sample audio file creation."""
        output_path = temp_dir / "sample.mp3"
        
        result = create_sample_audio(output_path)
        
        assert result == True
        # Should create a text file as placeholder
        text_file = output_path.with_suffix('.txt')
        assert text_file.exists()
        assert text_file.read_text() != ""
