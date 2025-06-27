"""
Test configuration for EdutainmentForge.

Sets up test environment and shared fixtures.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

# Test configuration
@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config(temp_dir):
    """Create sample configuration for tests."""
    return {
        'ms_learn_api_key': 'test_key',
        'ms_learn_base_url': 'https://docs.microsoft.com',
        'tts_service': 'azure',
        'tts_api_key': 'test_tts_key',
        'tts_region': 'eastus',
        'tts_voice': 'en-US-AriaNeural',
        'audio_format': 'mp3',
        'audio_quality': 'high',
        'output_directory': temp_dir / 'output',
        'debug': True,
        'log_level': 'DEBUG',
        'temp_directory': temp_dir / 'temp',
    }


@pytest.fixture
def sample_content():
    """Sample MS Learn content for testing."""
    return {
        'title': 'Test Module: Introduction to Cloud Computing',
        'content': '''
        Cloud computing is the delivery of computing services including servers, 
        storage, databases, networking, software, analytics, and intelligence over 
        the Internet to offer faster innovation, flexible resources, and economies 
        of scale.
        
        The main benefits of cloud computing include cost savings, speed, global 
        scale, productivity, performance, and reliability.
        ''',
        'url': 'https://docs.microsoft.com/test-module'
    }


@pytest.fixture
def mock_tts_service():
    """Mock TTS service for testing."""
    mock = Mock()
    mock.synthesize_text.return_value = True
    mock.get_available_voices.return_value = {
        'en-US-AriaNeural': 'Aria (US English, Female)',
        'en-US-GuyNeural': 'Guy (US English, Male)'
    }
    return mock
