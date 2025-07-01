# EdutainmentForge 🎙️

Transform Microsoft Learn content into engaging, conversational podcasts with AI-powered multi-voice narration.

## 📊 **Current Status: Production Ready with Premium AI Features**

✅ **Azure Speech Service**: Standard (S0) tier with premium neural voices and SSML styling  
✅ **Azure OpenAI**: GPT-4o and GPT-4o-mini with smart model selection  
✅ **Multi-Voice TTS**: Enhanced conversational styles (Sarah: conversation, Mike: friendly)  
✅ **Premium Integration**: Simplified, maintainable architecture with deprecated modules removed  
✅ **Repository**: Clean, organized codebase with proper backup management  

**Last Tested**: July 1, 2025 with Microsoft Learn Zero Trust content - ✅ **Working Perfectly**

## 🚀 Features

- **Multi-Voice Podcasts**: Two-host dialogue format with distinct male and female voices (Sarah & Mike)
- **AI-Enhanced Dialogue**: Azure OpenAI-powered script enhancement for more interactive, balanced conversations
-### Recent Improvements

### v2.0.0 - Premium AI Enhancement & Modern Development
- **Premium Service Integration** - GPT-4 support and neural voice capabilities for professional podcast quality
- **Modern Python Package Structure** - pyproject.toml, proper testing framework, and development automation
- **Azure AI Foundry Integration** - Built-in cost monitoring and usage analytics
- **Enhanced Security** - Comprehensive Key Vault integration with managed identity
- **Professional Development Tools** - Pre-commit hooks, automated testing, and quality assurance

### v1.3.0 - AI-Enhanced Dialogue & Security
- **Azure OpenAI Integration** - AI-powered script enhancement for more interactive, balanced conversations
- **Enhanced Table Processing** - Intelligent table detection and conversational summarization
- **Security Best Practices** - Environment-based secrets management with Azure Key Vault support
- **Production Ready** - Secure containerized deployment with Azure Container Apps
- **Improved Content Processing** - Better handling of complex Microsoft Learn content structures Content Processing**: Automatically cleans and converts technical documentation into natural conversation
- **Enhanced Table Handling**: Intelligent table detection and conversational summarization
- **Streamlined Intro**: Concise, listener-friendly podcast introductions (no more verbose descriptions!)
- **Robust Error Handling**: Comprehensive error handling with caching and retry mechanisms
- **Batch Processing**: Handle multiple URLs or entire learning paths at once
- **Web Interface**: Modern, responsive UI for easy podcast generation
- **Azure Cloud Ready**: Production deployment with Azure Container Apps
- **Secure Configuration**: Environment-based secrets management with Azure best practices
- **Local Storage**: All podcasts stored locally in WAV format with intelligent caching
- **CLI Support**: Command-line interface for automated workflows
- **Test Coverage**: Comprehensive test suite for reliability

## 🎯 What It Does

EdutainmentForge takes dry, technical Microsoft Learn documentation and transforms it into:
- Natural, conversational dialogue between two podcast hosts
- **AI-enhanced interactions** with balanced dialogue using Azure OpenAI
- **Intelligent table processing** that converts complex data into conversational insights
- **Short, engaging introductions** that get straight to the content
- Proper pronunciation of technical terms and abbreviations
- Clean, professional audio with distinct voices for each speaker
- Cached audio segments for faster re-generation
- Production-ready podcasts with robust error handling

## 🛠️ Technical Stack

### Core Dependencies
- **Python 3.8+** - Primary language with modern features
- **Flask 3.0+** - Web framework for the UI and API
- **Requests & BeautifulSoup4** - Web scraping for Microsoft Learn content
- **Azure Cognitive Services Speech** - Multi-voice text-to-speech synthesis
- **Azure OpenAI** - AI-powered script enhancement (optional)
- **PyDub** - Audio processing and manipulation
- **python-dotenv** - Environment variable management

### Standard Library Modules Used
- **pathlib** - Modern path handling
- **threading** - Background processing for web interface
- **uuid** - Unique ID generation for tracking
- **argparse** - Command-line argument parsing
- **tempfile** - Temporary file management for audio processing
- **json** - Data serialization
- **re** - Regular expressions for text processing
- **hashlib** - Caching and content identification
- **urllib.parse** - URL parsing and manipulation
- **abc** - Abstract base classes for service interfaces
- **io** - Binary stream handling for audio

### Development & Testing
- **pytest** - Testing framework
- **pytest-mock** - Mocking for unit tests
- **unittest.mock** - Built-in mocking (used in existing tests)

### Production Dependencies
- **gunicorn** - WSGI server for production deployment
- **Docker** - Containerization
- **Azure Container Apps** - Cloud hosting platform

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Azure Speech Service API key ([Get one free](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/))
- Azure OpenAI Service (optional, for AI-enhanced dialogue)
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

3. **Configure Azure Services**
   
   **For Local Development:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Azure Speech Service credentials
   # Optionally add Azure OpenAI credentials for AI-enhanced dialogue
   ```
   
   **For Production (Azure Key Vault):**
   All secrets are automatically retrieved from Azure Key Vault:
   - `azure-speech-key` → Azure Speech Services API key
   - `azure-speech-region` → Azure Speech Services region
   - `azure-openai-endpoint` → Azure OpenAI endpoint
   - `azure-openai-api-key` → Azure OpenAI API key
   - `azure-openai-api-version` → Azure OpenAI API version
   - `azure-openai-deployment-name` → Azure OpenAI deployment name

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

Deploy to Azure Container Apps with integrated Key Vault secret management:

```bash
# Build and push to Azure Container Registry
./deploy-to-azure.sh

# The container app automatically uses:
# - Azure Key Vault for secret management
# - Managed Identity for authentication
# - RBAC permissions for secure access
```

**Production Features:**
- ✅ **Azure Key Vault Integration** - All secrets managed securely
- ✅ **Managed Identity Authentication** - No stored credentials
- ✅ **RBAC Security** - Least privilege access
- ✅ **Environment Variable Fallback** - Robust configuration
- ✅ **Container Security** - Vulnerability scanning enabled

**Live Production URL:** `https://edutainmentforge-app.happymeadow-088e7533.eastus.azurecontainerapps.io/`

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

## 🤖 AI Enhancement (Optional)

EdutainmentForge supports Azure OpenAI integration to create more interactive and balanced dialogue between podcast hosts.

### Azure OpenAI Setup

1. **Create Azure OpenAI Resource**
   ```bash
   az cognitiveservices account create \
     --name "your-openai-resource" \
     --resource-group "your-resource-group" \
     --location "eastus2" \
     --kind "OpenAI" \
     --sku "S0"
   ```

2. **Deploy GPT Model**
   ```bash
   az cognitiveservices account deployment create \
     --name "your-openai-resource" \
     --resource-group "your-resource-group" \
     --deployment-name "gpt-4o-mini" \
     --model-name "gpt-4o-mini" \
     --model-version "2024-07-18" \
     --sku-capacity 10 \
     --sku-name "Standard"
   ```

3. **Configure Environment Variables**
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
   ```

### AI Enhancement Features
- **Interactive Dialogue**: Transforms monologue content into balanced conversations
- **Natural Transitions**: Creates smooth topic transitions between hosts
- **Technical Simplification**: Makes complex topics more accessible
- **Engagement Optimization**: Adds appropriate questions and responses between hosts

## 🔒 Security & Key Vault Integration

### Production Secret Management
EdutainmentForge integrates with **Azure Key Vault** for secure secret management in production environments.

#### Key Vault Configuration
The application automatically retrieves secrets from Azure Key Vault when deployed to Azure:

```env
# Key Vault URL
AZURE_KEY_VAULT_URL=https://edutainmentforge-kv.vault.azure.net/
```

#### Stored Secrets
The following secrets are managed in Azure Key Vault:
- `azure-speech-key` - Azure Speech Services API key
- `azure-speech-region` - Azure Speech Services region
- `azure-openai-endpoint` - Azure OpenAI service endpoint
- `azure-openai-api-key` - Azure OpenAI API key
- `azure-openai-api-version` - Azure OpenAI API version
- `azure-openai-deployment-name` - Azure OpenAI deployment name

#### Fallback Mechanism
The application uses a robust fallback system:
1. **Primary**: Azure Key Vault (production)
2. **Fallback**: Environment variables (development/local)

```python
# Automatic Key Vault integration with environment fallback
from utils.config import load_config

config = load_config()  # Automatically loads from Key Vault or env vars
```

### Azure Managed Identity
Production deployment uses Azure Managed Identity for secure Key Vault access:
- **No stored credentials** in container images
- **System-assigned managed identity** for Key Vault access
- **RBAC permissions** with "Key Vault Secrets User" role

### Security Best Practices
- **Never commit** `.env` files or API keys to version control
- **Azure Key Vault** for all production secrets
- **Managed Identity** authentication (no stored credentials)
- **Least privilege** RBAC permissions
- **Environment variable fallback** for local development
- **Regular security updates** and vulnerability scanning

## 📁 Project Structure

```
edutainmentforge/
├── app.py                    # Flask web application
├── podcast_cli.py            # Command-line interface  
├── Makefile                  # Development task automation
├── pyproject.toml            # Modern Python project configuration
├── DEPLOYMENT.md             # Comprehensive deployment guide
├── CHANGELOG.md              # Structured version history
├── README.md                 # Main project documentation
├── .github/
│   └── copilot-instructions.md # Enhanced GitHub Copilot guidelines
├── src/
│   ├── edutainmentforge/     # Package entry point
│   │   ├── __init__.py       # Package metadata
│   │   └── cli.py           # CLI entry point
│   ├── content/              # Content processing modules
│   │   ├── fetcher.py        # Microsoft Learn content fetching
│   │   ├── processor.py      # Content transformation to dialogue
│   │   └── ai_enhancer.py    # Azure OpenAI script enhancement
│   ├── audio/                # Multi-voice TTS services
│   │   ├── tts.py           # Core TTS service with Azure integration
│   │   └── multivoice_tts.py # Multi-voice coordination
│   ├── batch/                # Batch processing utilities
│   │   └── processor.py      # Batch URL processing
│   └── utils/                # Core utilities
│       ├── cache.py          # Audio caching system
│       ├── config.py         # Environment & Key Vault configuration
│       ├── keyvault.py       # Azure Key Vault integration
│       └── logger.py         # Logging configuration
├── tests/                    # Comprehensive test suite
│   ├── unit/                 # Unit tests with mocking
│   └── integration/          # Integration tests (including Key Vault)
├── templates/                # HTML templates for web interface
├── output/                   # Generated podcasts and scripts
├── cache/                    # Cached audio segments
├── logs/                     # Application logs
├── temp/                     # Temporary processing files
├── azure-infrastructure.bicep # Infrastructure as Code
├── azure-container-app.yaml  # Container deployment config
├── Dockerfile                # Container configuration
├── requirements.txt          # Core dependencies
├── requirements-dev.txt      # Development dependencies
└── docker-compose.yml        # Local development setup
```

## 🔧 Configuration

Environment variables in `.env`:

### Required
- `AZURE_SPEECH_KEY`: Your Azure Speech Service key
- `AZURE_SPEECH_REGION`: Azure region (e.g., "eastus2")

### Optional (for AI enhancement)
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_API_VERSION`: API version (default: "2024-02-15-preview")
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployed model name (e.g., "gpt-4o-mini")

### Voice Configuration
- `SARAH_VOICE`: Voice for female host (default: "en-US-AriaNeural")
- `MIKE_VOICE`: Voice for male host (default: "en-US-DavisNeural")

## 🛠️ Development

### Quick Development Setup
```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run the application
make run
```

### Testing Framework
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for quality assurance

## 🆕 Recent Improvements

### v1.3.0 - AI-Enhanced Dialogue & Security
- **Azure OpenAI Integration** - AI-powered script enhancement for more interactive, balanced conversations
- **Enhanced Table Processing** - Intelligent table detection and conversational summarization
- **Security Best Practices** - Environment-based secrets management with Azure Key Vault support
- **Production Ready** - Secure containerized deployment with Azure Container Apps
- **Improved Content Processing** - Better handling of complex Microsoft Learn content structures

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
