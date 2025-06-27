# EdutainmentForge

An application that converts Microsoft Learn content into engaging, edutainment-style podcasts.

## Overview

EdutainmentForge transforms dry educational content from Microsoft Learn into entertaining podcast episodes, making learning more engaging and accessible. The app fetches content from MS Learn, processes it into conversational scripts, and generates high-quality audio podcasts.

## Features

- Fetch content from Microsoft Learn modules
- Convert technical content into engaging podcast scripts
- Generate high-quality audio using text-to-speech
- Simple web interface for content selection and podcast generation
- Support for multiple modules and playlist creation

## Project Structure

```
EdutainmentForge/
├── README.md                 # This file
├── docs/                     # Additional documentation
├── src/                      # Source code
│   ├── content/             # MS Learn content fetching and processing
│   ├── audio/               # Text-to-speech and audio processing
│   ├── ui/                  # User interface components
│   └── utils/               # Utility functions and helpers
├── tests/                   # Automated tests
├── assets/                  # Static assets (samples, media)
├── scripts/                 # Development and deployment scripts
└── .github/                 # GitHub-specific configuration
```

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Azure Speech Service (see Configuration section)
4. Set up environment variables (see Configuration section)
5. Run the application: `python3 podcast_cli.py [URL]`

## Configuration

### Azure Speech Service Setup

EdutainmentForge uses Azure Cognitive Services Speech for high-quality text-to-speech. To set up:

1. **Create an Azure Speech Service resource**:
   ```bash
   az cognitiveservices account create \
       --name "edutainmentforge-speech" \
       --resource-group "your-resource-group" \
       --kind "SpeechServices" \
       --sku "S0" \
       --location "eastus2"
   ```

2. **Get your API key**:
   ```bash
   az cognitiveservices account keys list \
       --name "edutainmentforge-speech" \
       --resource-group "your-resource-group"
   ```

### Environment Variables

Create a `.env` file in the root directory with the following variables:

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

### Usage Examples

```bash
# Process a Microsoft Learn unit into a podcast
python3 podcast_cli.py "https://learn.microsoft.com/training/modules/get-started-ai-fundamentals/1-introduction"

# Use a specific voice
python3 podcast_cli.py [URL] --voice "en-US-DavisNeural"

# Custom output filename
python3 podcast_cli.py [URL] --output "My_Custom_Podcast"

# List available voices
python3 podcast_cli.py --list-voices
```

## Development

This project follows iterative development with continuous testing. See `docs/development-guide.md` for detailed development guidelines.

### Testing

Run tests with: `pytest tests/`

### Code Style

We follow PEP 8 for Python code. Use the provided linting configuration:
- `flake8` for style checking
- `black` for code formatting

## Contributing

See `CONTRIBUTING.md` for contribution guidelines and coding standards.

## License

MIT License - see `LICENSE` file for details.
