import pytest
from unittest.mock import patch, MagicMock
from pydub import AudioSegment

# Import the module under test
import audio.speechGeneration as sg

@pytest.fixture
def dummy_audio():
    return MagicMock(spec=AudioSegment)

def test_generate_speech_cache_hit(dummy_audio):
    # Mock the imported functions by their actual import path in the module
    with patch('utils.cache.get_cached_audio', return_value=dummy_audio) as mock_get_cache, \
         patch('utils.logger.logger') as mock_logger:
        result = sg.generate_speech('<speak>Hello</speak>', 'en-US-TestVoice')
        assert result == dummy_audio
        mock_get_cache.assert_called_once()
        # Check that info was called with a message containing 'Cache hit for key'
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert 'Cache hit for key' in call_args

def test_generate_speech_cache_miss_and_success(dummy_audio):
    with patch('utils.cache.get_cached_audio', return_value=None), \
         patch('audio.speechGeneration.call_tts_service', return_value=dummy_audio) as mock_tts, \
         patch('utils.cache.cache_audio') as mock_cache_audio, \
         patch('utils.logger.logger') as mock_logger:
        result = sg.generate_speech('<speak>Hi</speak>', 'en-US-TestVoice')
        assert result == dummy_audio
        mock_tts.assert_called_once()
        mock_cache_audio.assert_called_once()
        # Check that info was called with a message containing 'Generated and cached audio for key'
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert 'Generated and cached audio for key' in call_args

def test_generate_speech_tts_service_failure():
    with patch('utils.cache.get_cached_audio', return_value=None), \
         patch('audio.speechGeneration.call_tts_service', side_effect=Exception('TTS error')), \
         patch('utils.logger.logger') as mock_logger:
        # Import SpeechGenerationError from the module
        SpeechGenerationError = getattr(sg, 'SpeechGenerationError', Exception)
        with pytest.raises(SpeechGenerationError) as excinfo:
            sg.generate_speech('<speak>Fail</speak>', 'en-US-TestVoice')
        assert 'Speech generation failed' in str(excinfo.value)
        mock_logger.error.assert_called_once()

def test_generate_speech_empty_ssml(dummy_audio):
    with patch('utils.cache.get_cached_audio', return_value=None), \
         patch('audio.speechGeneration.call_tts_service', return_value=dummy_audio):
        result = sg.generate_speech('', 'en-US-TestVoice')
        assert result == dummy_audio

def test_generate_speech_invalid_voice(dummy_audio):
    with patch('utils.cache.get_cached_audio', return_value=None), \
         patch('audio.speechGeneration.call_tts_service', return_value=dummy_audio):
        result = sg.generate_speech('<speak>Test</speak>', '')
        assert result == dummy_audio
