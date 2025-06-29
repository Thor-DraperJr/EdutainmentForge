# EdutainmentForge 🎙️

Transform Microsoft Learn content into engaging, conversational podcasts with AI-powered multi-voice narration.

## 🚀 Features

- **Multi-Voice Podcasts**: Two-host dialogue format with distinct male and female voices (Sarah & Mike)
- **Smart Content Processing**: Automatically cleans and converts technical documentation into natural conversation
- **Streamlined Intro**: Concise, listener-friendly podcast introductions (no more verbose descriptions!)
- **Robust Error Handling**: Comprehensive error handling with caching and retry mechanisms
- **Batch Processing**: Handle multiple URLs or entire learning paths at once
- **Web Interface**: Modern, responsive UI for easy podcast generation
- **Azure Cloud Ready**: Production deployment with Azure Container Apps
- **Local Storage**: All podcasts stored locally in WAV format with intelligent caching
- **CLI Support**: Command-line interface for automated workflows
- **Test Coverage**: Comprehensive test suite for reliability

## 🎯 What It Does

EdutainmentForge takes dry, technical Microsoft Learn documentation and transforms it into:
- Natural, conversational dialogue between two podcast hosts
- **Short, engaging introductions** that get straight to the content
- Proper pronunciation of technical terms and abbreviations
- Clean, professional audio with distinct voices for each speaker
- Cached audio segments for faster re-generation
- Production-ready podcasts with robust error handling

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Azure Speech Service API key ([Get one free](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/))
- ffmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/edutainmentforge.git
   cd edutainmentforge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Azure Speech Service**
   ```bash
   cp .env.example .env
   # Edit .env and add your Azure Speech Service credentials
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to start creating podcasts!

### Docker Deployment

For containerized deployment:

```bash
# Build and run with Docker Compose
./docker-helper.sh build
./docker-helper.sh run

# Or manually
docker-compose up -d
```

### Azure Deployment

Deploy to Azure Container Apps for production:

```bash
# Build and push to Azure Container Registry
./deploy-to-azure.sh

# Deploy using Azure Container Apps
az containerapp update --name edutainmentforge-app \
  --resource-group edutainmentforge-rg \
  --image edutainmentforge.azurecr.io/edutainmentforge:latest
```

## 📖 Usage

### Web Interface
1. Open `http://localhost:5000`
2. Enter a Microsoft Learn URL
3. Click "Generate Podcast"
4. Download your multi-voice podcast!

### Command Line
```bash
python podcast_cli.py --url "https://learn.microsoft.com/en-us/training/modules/intro-to-azure-ai/" --output "my_podcast"
```

### Batch Processing
```bash
python podcast_cli.py --batch urls.txt --output "learning_path_batch"
```

## 🎨 Voice Configuration

Customize the voices in your `.env` file:
```env
SARAH_VOICE=en-US-AriaNeural     # Female host
MIKE_VOICE=en-US-DavisNeural     # Male host
NARRATOR_VOICE=en-US-JennyNeural # Fallback voice
```

## 📁 Project Structure

```
edutainmentforge/
├── app.py                 # Flask web application
├── podcast_cli.py         # Command-line interface
├── src/
│   ├── content/          # Content fetching and processing
│   │   ├── fetcher.py    # Microsoft Learn content fetching
│   │   └── processor.py  # Content transformation to dialogue
│   ├── audio/            # Multi-voice TTS services
│   │   ├── speechGeneration.py  # Core TTS with caching
│   │   ├── multivoice_tts.py   # Multi-voice coordination
│   │   ├── ssmlFormatter.py    # SSML formatting
│   │   └── test_speechGeneration.py  # Test suite
│   ├── batch/            # Batch processing utilities
│   └── utils/            # Core utilities
│       ├── cache.py      # Audio caching system
│       ├── logger.py     # Logging configuration
│       └── config.py     # Environment configuration
├── templates/            # HTML templates for web interface
├── output/              # Generated podcasts and scripts
├── cache/               # Cached audio segments
├── azure-*.yaml         # Azure deployment configurations
└── requirements.txt     # Python dependencies
```

## 🔧 Configuration

Environment variables in `.env`:
- `AZURE_SPEECH_KEY`: Your Azure Speech Service key
- `AZURE_SPEECH_REGION`: Azure region (e.g., "eastus2")
- `SARAH_VOICE`: Voice for female host
- `MIKE_VOICE`: Voice for male host

## 🆕 Recent Improvements

### v1.2.0 - Enhanced User Experience & Robustness
- **Dramatically shortened podcast introductions** - No more verbose descriptions, straight to the content
- **Comprehensive test suite** - Robust error handling and caching validation
- **Cleaned codebase** - Removed unused modules and redundant code
- **Enhanced Azure deployment** - Production-ready with container apps
- **Improved caching system** - Faster regeneration of previously processed content
- **Better error handling** - Graceful failure recovery and detailed logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
