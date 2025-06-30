"""
Configuration management for EdutainmentForge.

Handles loading and validating configuration from environment variables and Azure Key Vault.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def _get_secret_with_fallback(secret_name: str, env_var_name: str, default: str = None) -> Optional[str]:
    """
    Get a secret from Key Vault with environment variable fallback.
    
    Args:
        secret_name: Name of secret in Key Vault (with hyphens)
        env_var_name: Environment variable name (with underscores)
        default: Default value if neither source has the value
        
    Returns:
        Secret value or default
    """
    # Try Key Vault first if available
    try:
        from utils.keyvault import get_secret_with_fallback
        return get_secret_with_fallback(secret_name, env_var_name) or default
    except ImportError:
        # Key Vault libraries not available, use environment variable only
        return os.getenv(env_var_name, default)
    except Exception as e:
        # Key Vault error, fallback to environment variable
        return os.getenv(env_var_name, default)


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and Azure Key Vault.
    
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
        
        # Text-to-Speech configuration with Key Vault fallback
        "tts_service": os.getenv("TTS_SERVICE", "azure"),
        "tts_api_key": _get_secret_with_fallback("azure-speech-key", "TTS_API_KEY") or 
                      _get_secret_with_fallback("azure-speech-key", "AZURE_SPEECH_KEY"),
        "tts_region": _get_secret_with_fallback("azure-speech-region", "TTS_REGION") or 
                     _get_secret_with_fallback("azure-speech-region", "AZURE_SPEECH_REGION", "eastus"),
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
        
        # Azure OpenAI configuration for script enhancement with Key Vault fallback
        "azure_openai_endpoint": _get_secret_with_fallback("azure-openai-endpoint", "AZURE_OPENAI_ENDPOINT"),
        "azure_openai_api_key": _get_secret_with_fallback("azure-openai-api-key", "AZURE_OPENAI_API_KEY"),
        "azure_openai_api_version": _get_secret_with_fallback("azure-openai-api-version", "AZURE_OPENAI_API_VERSION", "2024-02-01"),
        "azure_openai_deployment": _get_secret_with_fallback("azure-openai-deployment-name", "AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        
        # Key Vault configuration
        "azure_key_vault_url": os.getenv("AZURE_KEY_VAULT_URL", "https://edutainmentforge-kv.vault.azure.net/"),
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

# Text-to-Speech Service (required - can be stored in Azure Key Vault)
TTS_SERVICE=azure
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus

# Multi-voice configuration
SARAH_VOICE=en-US-AriaNeural
MIKE_VOICE=en-US-DavisNeural
NARRATOR_VOICE=en-US-JennyNeural

# Azure OpenAI (optional - can be stored in Azure Key Vault)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Azure Key Vault (for production secret management)
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Audio Settings
AUDIO_FORMAT=mp3
AUDIO_QUALITY=high
OUTPUT_DIR=output

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
TEMP_DIR=temp
"""
