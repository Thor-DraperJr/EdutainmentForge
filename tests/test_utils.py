"""
Tests for utility functions.
"""

import pytest
import os
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, ConfigError, setup_logger, get_logger


class TestConfig:
    """Test cases for configuration management."""
    
    def test_load_config_minimal(self):
        """Test loading minimal configuration."""
        # Set minimal required environment
        os.environ['TTS_API_KEY'] = 'test_key'
        
        try:
            config = load_config()
            
            assert 'tts_api_key' in config
            assert config['tts_api_key'] == 'test_key'
            assert 'output_directory' in config
            assert 'debug' in config
            
            # Clean up
            del os.environ['TTS_API_KEY']
            
        except ConfigError:
            # Clean up on error
            if 'TTS_API_KEY' in os.environ:
                del os.environ['TTS_API_KEY']
            raise
    
    def test_load_config_missing_required(self):
        """Test loading config with missing required values."""
        # Ensure no TTS key is set
        if 'TTS_API_KEY' in os.environ:
            del os.environ['TTS_API_KEY']
        
        with pytest.raises(ConfigError):
            load_config()
    
    def test_load_config_with_env_file(self, temp_dir):
        """Test loading config with .env file."""
        # Create temporary .env file
        env_file = temp_dir / '.env'
        env_content = """
TTS_API_KEY=test_from_file
DEBUG=true
LOG_LEVEL=DEBUG
"""
        env_file.write_text(env_content)
        
        # Temporarily change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = load_config()
            
            assert config['tts_api_key'] == 'test_from_file'
            assert config['debug'] == True
            assert config['log_level'] == 'DEBUG'
            
        finally:
            os.chdir(original_cwd)


class TestLogging:
    """Test cases for logging functionality."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger(name='test_logger')
        
        assert logger.name == 'test_logger'
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_file(self, temp_dir):
        """Test logger setup with file output."""
        log_file = temp_dir / 'test.log'
        logger = setup_logger(name='test_file_logger', log_file=log_file)
        
        assert logger.name == 'test_file_logger'
        assert len(logger.handlers) >= 2  # Console + file handler
        
        # Test logging
        logger.info("Test message")
        
        # Check if log file was created
        assert log_file.exists()
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger('test_module')
        
        assert 'edutainment_forge.test_module' in logger.name
    
    def test_setup_logger_idempotent(self):
        """Test that setup_logger doesn't add duplicate handlers."""
        logger1 = setup_logger(name='idempotent_test')
        handler_count1 = len(logger1.handlers)
        
        logger2 = setup_logger(name='idempotent_test')
        handler_count2 = len(logger2.handlers)
        
        assert handler_count1 == handler_count2
        assert logger1 is logger2
