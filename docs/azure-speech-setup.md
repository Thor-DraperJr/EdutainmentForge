# Azure Speech Service Setup Guide

## Overview

EdutainmentForge now supports high-quality text-to-speech using Azure Cognitive Services Speech SDK. This guide covers the setup, configuration, and usage of Azure Speech Services for generating podcast audio.

## Prerequisites

1. **Azure Subscription**: You need an active Azure subscription
2. **Speech Service Resource**: Create a Speech service resource in Azure
3. **API Key and Region**: Obtain the API key and region from your Speech service

## Azure Setup

### 1. Create Speech Service Resource

```bash
# Using Azure CLI
az cognitiveservices account create \
    --name "edutainmentforge-speech" \
    --resource-group "your-resource-group" \
    --kind "SpeechServices" \
    --sku "S0" \
    --location "eastus2"
```

### 2. Get API Key and Endpoint

```bash
# Get the API key
az cognitiveservices account keys list \
    --name "edutainmentforge-speech" \
    --resource-group "your-resource-group"

# Get the region
az cognitiveservices account show \
    --name "edutainmentforge-speech" \
    --resource-group "your-resource-group" \
    --query "location"
```

## Configuration

### Environment Variables

Update your `.env` file with the Azure Speech Service credentials:

```bash
# Azure Speech Services (required for TTS)
TTS_SERVICE=azure
TTS_API_KEY=your_api_key_here
TTS_REGION=eastus2
TTS_VOICE=en-US-AriaNeural

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
OUTPUT_DIR=output
TEMP_DIR=temp
```

### Supported Voices

Azure Speech Service supports many neural voices. Common options:

- **English (US)**:
  - `en-US-AriaNeural` - Female, expressive
  - `en-US-GuyNeural` - Male, friendly
  - `en-US-JennyNeural` - Female, assistant-like
  - `en-US-DavisNeural` - Male, conversational

- **English (UK)**:
  - `en-GB-LibbyNeural` - Female, British accent
  - `en-GB-RyanNeural` - Male, British accent

## Installation

Install the required dependencies:

```bash
pip install azure-cognitiveservices-speech>=1.34.0
```

## Usage

### Basic Usage

```python
from src.audio.tts import create_tts_service
from src.utils.config import load_config

# Load configuration
config = load_config()

# Create TTS service (automatically detects Azure)
tts_service = create_tts_service(config)

# Generate audio
success = tts_service.synthesize_text(
    text="Hello from EdutainmentForge!",
    output_path=Path("output/hello.wav")
)
```

### Full Pipeline

```python
# Process Microsoft Learn content to podcast
python3 src/main.py --url "https://learn.microsoft.com/training/modules/..."
```

## Testing

### Quick Test

```bash
# Test Azure Speech Service
python3 simple_azure_test.py
```

### Full Pipeline Test

```bash
# Test complete pipeline with existing script
python3 test_full_pipeline.py
```

## Features

### Audio Quality
- **Format**: WAV (16-bit, 16kHz)
- **Quality**: High-quality neural voices
- **Compression**: Uncompressed for best quality

### Voice Customization
- Multiple neural voices available
- Adjustable speaking rate and pitch via SSML
- Support for different languages and accents

### Error Handling
- Automatic fallback to local TTS if Azure fails
- Retry logic for transient failures
- Detailed error logging

## Troubleshooting

### Common Issues

1. **"Invalid API Key"**
   - Verify your API key in `.env`
   - Check that the Speech service resource is active
   - Ensure the key hasn't expired

2. **"Region Not Found"**
   - Verify the region matches your Speech service location
   - Common regions: `eastus`, `eastus2`, `westus2`, `centralus`

3. **"Audio File Not Generated"**
   - Check output directory permissions
   - Verify sufficient disk space
   - Check network connectivity to Azure

4. **"SDK Import Error"**
   ```bash
   pip install azure-cognitiveservices-speech
   ```

### Debugging

Enable debug logging:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

Check logs for detailed error information.

## Performance

### Optimization Tips

1. **Batch Processing**: Process multiple units together
2. **Voice Caching**: Reuse TTS service instances
3. **Network**: Use regions close to your location
4. **Text Length**: Optimal chunks are 1000-5000 characters

### Limits

- **Characters per request**: 10,000 characters maximum
- **Requests per second**: Varies by pricing tier
- **Monthly quota**: Based on your Azure subscription

## Cost Management

### Pricing
- **Standard**: $4 per 1M characters
- **Neural voices**: $16 per 1M characters
- **Free tier**: 5,000 characters per month

### Cost Optimization
- Use appropriate voice types for content
- Cache generated audio when possible
- Monitor usage through Azure portal

## Next Steps

1. **Voice Customization**: Experiment with different voices
2. **SSML Integration**: Add speech markup for better control
3. **Batch Processing**: Process multiple modules efficiently
4. **Quality Enhancement**: Add post-processing effects

## Resources

- [Azure Speech Service Documentation](https://docs.microsoft.com/azure/cognitive-services/speech-service/)
- [Voice Samples](https://speech.microsoft.com/portal/voicegallery)
- [SSML Reference](https://docs.microsoft.com/azure/cognitive-services/speech-service/speech-synthesis-markup)
- [Pricing Information](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/)
