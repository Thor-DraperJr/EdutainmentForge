# EdutainmentForge 🎙️

Transform Microsoft Learn content into engaging, conversational podcasts with AI-powered multi-voice narration.

## 🎧 The Vision Behind EdutainmentForge

As an auditory learner, I created EdutainmentForge to solve a real problem in technical education. Traditional documentation—walls of text, complex diagrams, and dense code samples—creates barriers for many learners. This project demonstrates how modern AI systems can transform learning experiences when thoughtfully architected.

EdutainmentForge represents the intersection of:
- **Accessibility Engineering**: Making technical content available to diverse learning styles
- **AI Systems Integration**: Orchestrating multiple AI services into a cohesive product
- **Content Intelligence**: Applying AI to understand and transform complex information structures
- **Voice Computing**: Leveraging neural TTS for natural, engaging audio experiences

## 🔬 Technical Architecture Highlights

The project showcases several advanced AI and cloud engineering techniques:

1. **Multi-Service AI Orchestration**: Seamlessly coordinates Azure OpenAI for content processing with Azure Speech Services for voice synthesis, demonstrating expertise in complex AI system design.

2. **Content Structure Analysis**: Implements intelligent parsing of technical documentation, recognizing headers, code blocks, and tables to transform them appropriately—turning data structures into natural dialogue.

3. **Dialogue Generation System**: Employs GPT-4o to convert technical monologues into balanced, engaging conversations between two hosts, showing practical application of generative AI beyond simple prompting.

4. **Neural Voice Engineering**: Uses premium TTS voices with custom SSML styling for natural-sounding conversations with appropriate emphasis, pacing, and technical pronunciation.

5. **Enterprise-Grade Architecture**: Implements production-ready patterns including managed identity authentication, secure Key Vault integration, containerized deployment, and comprehensive caching strategies.

## 📊 Current Status & Features

✅ **Azure Speech Service**: Premium neural voices with SSML styling  
✅ **Azure OpenAI**: GPT-4o and GPT-4o-mini with smart model selection  
✅ **Multi-Voice TTS**: Enhanced conversational styles with distinct hosts  
✅ **Security**: Key Vault integration with managed identity  
✅ **Enterprise-Ready**: Containerized with proper CI/CD pipelines  

**Last Tested**: July 1, 2025 with Microsoft Learn Zero Trust content - ✅ **Working Perfectly**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Azure Speech Service API key ([Get one free](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/))
- Azure OpenAI Service (optional)
- ffmpeg (for audio processing)

### Basic Setup

```bash
# Clone repository
git clone https://github.com/yourusername/edutainmentforge.git
cd edutainmentforge

# Install dependencies
pip install -r requirements.txt

# Configure environment (.env file)
cp .env.example .env
# Edit .env with your Azure credentials

# Run application
python app.py
```

Visit `http://localhost:5000` to start creating podcasts!

## 🎛️ Key Technologies

- **Azure Speech**: Premium neural voices for natural-sounding speech
- **Azure OpenAI**: Script enhancement with GPT-4o models
- **Python 3.8+**: Core application language
- **Flask**: Web interface
- **Docker**: Containerized deployment
- **Azure Container Apps**: Production hosting

## 📚 Documentation

For more detailed information, see the documentation files:

- [Detailed Features](docs/FEATURES.md) - Comprehensive feature list
- [Configuration Guide](docs/CONFIGURATION.md) - All configuration options
- [Development Guide](docs/DEVELOPMENT.md) - Setup and contribution guidelines
- [Azure Deployment](docs/AZURE_DEPLOYMENT.md) - Production deployment steps
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Project Board Guide](docs/PROJECT_BOARD.md) - Hackathon task tracking and team collaboration

## 📋 Project Management

EdutainmentForge uses a **GitHub Project Board** for hackathon task tracking and team collaboration:

🎯 **[View Project Board](https://github.com/Thor-DraperJr/EdutainmentForge/projects)** | 📝 **[Project Board Documentation](docs/PROJECT_BOARD.md)**

### Quick Project Board Overview
- **Backlog**: New issues and planned features
- **In Progress**: Active development work  
- **Review**: Code review and testing phase
- **Done**: Completed and merged work

All issues and pull requests are automatically organized on the project board with smart labeling and status updates.

## 📋 Recent Changes

### v2.0.0 - Premium AI Enhancement & Modern Development
- **Premium Service Integration** - GPT-4 support with neural voice capabilities
- **Modern Python Package Structure** - Improved development workflow
- **Azure AI Foundry Integration** - Built-in cost monitoring

### v1.3.0 - AI-Enhanced Dialogue & Security
- **Azure OpenAI Integration** - AI-powered script enhancement
- **Enhanced Table Processing** - Intelligent conversational summaries
- **Security Best Practices** - Key Vault integration

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
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
./scripts/docker-helper.sh build
./scripts/docker-helper.sh run

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
- `azure-ad-tenant-id` - Azure AD tenant ID for authentication
- `azure-ad-client-id` - Azure AD application client ID
- `azure-ad-client-secret` - Azure AD application client secret
- `flask-secret-key` - Flask session encryption key

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
