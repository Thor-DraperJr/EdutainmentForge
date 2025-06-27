"""
Configuration management for EdutainmentForge.

Handles loading and validating configuration from environment variables.
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary containing application configuration
        
    Raises:
        ConfigError: If required configuration is missing
    """
    # Load .env file if it exists
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    config = {
        # MS Learn API configuration
        "ms_learn_api_key": os.getenv("MS_LEARN_API_KEY"),
        "ms_learn_base_url": os.getenv("MS_LEARN_BASE_URL", "https://docs.microsoft.com"),
        
        # Text-to-Speech configuration
        "tts_service": os.getenv("TTS_SERVICE", "azure"),
        "tts_api_key": os.getenv("TTS_API_KEY"),
        "tts_region": os.getenv("TTS_REGION", "eastus"),
        "tts_voice": os.getenv("TTS_VOICE", "en-US-AriaNeural"),
        
        # Audio configuration
        "audio_format": os.getenv("AUDIO_FORMAT", "mp3"),
        "audio_quality": os.getenv("AUDIO_QUALITY", "high"),
        "output_directory": Path(os.getenv("OUTPUT_DIR", "output")),
        
        # Application settings
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "temp_directory": Path(os.getenv("TEMP_DIR", "temp")),
    }
    
    # Validate required configuration
    required_keys = ["tts_api_key"]
    missing_keys = [key for key in required_keys if not config[key]]
    
    if missing_keys:
        raise ConfigError(f"Missing required configuration: {', '.join(missing_keys)}")
    
    # Ensure directories exist
    config["output_directory"].mkdir(exist_ok=True)
    config["temp_directory"].mkdir(exist_ok=True)
    
    return config


def get_sample_config() -> str:
    """
    Get sample configuration file content.
    
    Returns:
        Sample .env file content as string
    """
    return """# EdutainmentForge Configuration

# Microsoft Learn API (optional for web scraping)
MS_LEARN_API_KEY=your_ms_learn_api_key_here
MS_LEARN_BASE_URL=https://docs.microsoft.com

# Text-to-Speech Service (required)
TTS_SERVICE=azure
TTS_API_KEY=your_azure_speech_key_here
TTS_REGION=eastus
TTS_VOICE=en-US-AriaNeural

# Audio Settings
AUDIO_FORMAT=mp3
AUDIO_QUALITY=high
OUTPUT_DIR=output

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
TEMP_DIR=temp
"""
