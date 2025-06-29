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
        "tts_api_key": os.getenv("TTS_API_KEY") or os.getenv("AZURE_SPEECH_KEY"),
        "tts_region": os.getenv("TTS_REGION") or os.getenv("AZURE_SPEECH_REGION", "eastus"),
        "tts_voice": os.getenv("TTS_VOICE", "en-US-AriaNeural"),
        
        # Multi-voice configuration for podcast hosts
        "sarah_voice": os.getenv("SARAH_VOICE", "en-US-AriaNeural"),
        "mike_voice": os.getenv("MIKE_VOICE", "en-US-DavisNeural"),
        "narrator_voice": os.getenv("NARRATOR_VOICE", "en-US-JennyNeural"),
        
        # Audio configuration
        "audio_format": os.getenv("AUDIO_FORMAT", "mp3"),
        "audio_quality": os.getenv("AUDIO_QUALITY", "high"),
        "output_directory": Path(os.getenv("OUTPUT_DIR", "output")),
        
        # Application settings
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "temp_directory": Path(os.getenv("TEMP_DIR", "temp")),
        
        # Azure OpenAI configuration for script enhancement
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "azure_openai_api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "azure_openai_api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
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
