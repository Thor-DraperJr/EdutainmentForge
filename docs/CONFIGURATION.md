# EdutainmentForge Configuration Guide

This guide covers all configuration options for EdutainmentForge.

## Environment Configuration

EdutainmentForge uses environment variables for configuration. In development, these are loaded from a `.env` file. In production, they are loaded from Azure Key Vault.

### Local Development

Create a `.env` file in the project root:

```env
# Azure Speech Service (Required)
AZURE_SPEECH_KEY=your_speech_key_here
AZURE_SPEECH_REGION=eastus2

# Azure OpenAI (Optional)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_openai_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Voice Configuration
SARAH_VOICE=en-US-AriaNeural
MIKE_VOICE=en-US-DavisNeural
NARRATOR_VOICE=en-US-JennyNeural

# Application Settings
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_DIR=./cache
OUTPUT_DIR=./output
```

### Production Environment

In production, all sensitive configurations are stored in Azure Key Vault:

- `azure-speech-key` - Azure Speech Services API key
- `azure-speech-region` - Azure Speech Services region
- `azure-openai-endpoint` - Azure OpenAI service endpoint
- `azure-openai-api-key` - Azure OpenAI API key
- `azure-openai-api-version` - Azure OpenAI API version
- `azure-openai-deployment-name` - Azure OpenAI deployment name
- `sarah-voice` - Voice for Sarah (female host)
- `mike-voice` - Voice for Mike (male host)

The application uses a robust fallback system:
1. **Primary**: Azure Key Vault (production)
2. **Fallback**: Environment variables (development/local)

### Key Vault Configuration

To configure Azure Key Vault integration:

```env
# Key Vault URL
AZURE_KEY_VAULT_URL=https://edutainmentforge-kv.vault.azure.net/
```

## Voice Configuration

### Available Voices

EdutainmentForge uses Azure's neural voices for natural-sounding speech:

| Role    | Default Voice      | Style        | Notes                              |
|---------|-------------------|--------------|-----------------------------------|
| Sarah   | en-US-AriaNeural  | conversation | Female host, primary explainer    |
| Mike    | en-US-DavisNeural | friendly     | Male host, asks questions         |
| Narrator| en-US-JennyNeural | assistant    | Fallback for single-voice mode    |

### Custom Voice Configuration

To customize voices, update these environment variables:

```env
SARAH_VOICE=en-US-EmmaNeural
MIKE_VOICE=en-US-GuyNeural
NARRATOR_VOICE=en-US-JennyNeural
```

## Azure OpenAI Configuration

EdutainmentForge supports Azure OpenAI integration for enhanced dialogue creation.

### Model Configuration

```env
# Azure OpenAI configuration
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini  # Model deployment name
AZURE_OPENAI_MAX_TOKENS=2000              # Maximum tokens per request
AZURE_OPENAI_TEMPERATURE=0.7              # Creativity level (0.0-1.0)
```

### Advanced OpenAI Settings

```env
# Advanced settings
AZURE_OPENAI_SYSTEM_MESSAGE_FILE=./prompts/system_message.txt  # Custom system message
AZURE_OPENAI_ENABLE_STREAMING=true                           # Stream responses
AZURE_OPENAI_REQUEST_TIMEOUT=60                              # Timeout in seconds
```

## Audio Settings

Customize audio generation settings:

```env
# Audio configuration
AUDIO_FORMAT=wav                # Output format (wav, mp3)
AUDIO_SAMPLE_RATE=24000         # Sample rate in Hz
AUDIO_BITRATE=192k              # Bitrate for MP3 encoding
ENABLE_AUDIO_NORMALIZATION=true # Normalize audio levels
```

## Cache Configuration

```env
# Cache configuration
CACHE_ENABLED=true              # Enable content caching
CACHE_DIR=./cache              # Cache directory
CACHE_MAX_AGE=604800           # Cache lifetime in seconds (7 days)
CACHE_CLEANUP_INTERVAL=86400   # Cleanup interval in seconds (1 day)
```
