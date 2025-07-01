# Changelog

All notable changes to EdutainmentForge will be documented in this file.

## [2.0.0] - 2024-Current

### 🚀 Major Features Added

#### 🤖 Azure OpenAI Integration
- **AI-Enhanced Dialogue**: Integrated Azure OpenAI (GPT-4o-mini) for intelligent script enhancement
- **Balanced Conversations**: AI transforms monologue content into engaging 50/50 dialogue between Sarah and Mike
- **Interactive Enhancements**: Added natural interruptions, follow-up questions, and conversational flow
- **Smart Table Processing**: Specialized AI enhancement for table content with comparative discussions
- **Cost-Effective**: Using GPT-4o-mini deployment for optimal cost/performance ratio

#### 🎯 Enhanced Multi-Voice TTS
- **Distinct Voice Mapping**: Sarah (AriaNeural) and Mike (DavisNeural) use different voices
- **Improved Script Parsing**: Enhanced dialogue parsing to properly recognize multiple speakers
- **Post-Processing Pipeline**: Added script cleaning to remove markdown formatting and replace symbols
- **Cache Optimization**: Audio segments cached by content hash to avoid regeneration

#### 🔐 Azure Key Vault Integration
- **Secure Secret Management**: All API keys stored in Azure Key Vault
- **Managed Identity**: System-assigned managed identity for secure access
- **RBAC Security**: Least privilege access with "Key Vault Secrets User" role
- **Fallback Support**: Environment variables as fallback for local development

### 🐛 Bug Fixes

#### 🔧 Audio Quality Issues
- **Fixed**: TTS saying "asterisk" by replacing symbols with pronounceable words
- **Fixed**: Voice separation issues where both hosts used the same voice
- **Fixed**: Dialogue segmentation problems that caused single narrator segments
- **Fixed**: Markdown artifacts and HTML entities in generated audio

#### 📝 Content Processing
- **Fixed**: Enhanced content fetcher to remove markdown artifacts
- **Fixed**: Symbol replacement for better TTS pronunciation
- **Fixed**: Format standardization for reliable TTS processing
- **Fixed**: Table content parsing and enhancement

### 🏗️ Infrastructure & Deployment

#### ☁️ Azure Container Apps
- **Container Registry**: Private Azure Container Registry integration
- **Managed Identity**: Secure authentication without stored credentials
- **Key Vault References**: Automatic secret resolution in production
- **Auto-scaling**: Container Apps automatic scaling based on demand

#### 🛡️ Security Enhancements
- **Zero Hardcoded Secrets**: All sensitive data moved to Key Vault
- **RBAC Permissions**: Proper role-based access control
- **Network Security**: Private container registry with managed access
- **Audit Logging**: Comprehensive logging for security monitoring

### 🧪 Testing & Quality

#### ✅ Test Framework
- **Pytest Integration**: Comprehensive unit test framework
- **Mock Services**: Azure service mocking for reliable testing
- **Cleanup Automation**: Automatic test file and cache cleanup
- **Coverage Reporting**: Test coverage tracking and reporting

#### 📊 Monitoring & Observability
- **Application Insights**: Detailed telemetry and performance monitoring
- **Log Analytics**: Centralized logging and analysis
- **Health Checks**: Container app health monitoring
- **Cost Tracking**: Azure service usage and cost monitoring

### 📚 Documentation

#### 📖 Comprehensive Guides
- **Deployment Guide**: Complete Azure deployment documentation
- **Security Guide**: Security best practices and implementation
- **Development Guide**: Local development setup and guidelines
- **API Documentation**: Detailed API and service documentation

#### 🎯 Developer Experience
- **Copilot Instructions**: Detailed GitHub Copilot integration guidelines
- **MCP Server Integration**: Model Context Protocol for Azure resource management
- **Code Standards**: Comprehensive coding standards and best practices
- **Troubleshooting**: Common issues and resolution guides

### 🔄 Breaking Changes

- **Configuration**: Moved from environment variables to Azure Key Vault for production
- **Authentication**: Now requires Azure CLI authentication for local development
- **Dependencies**: Added Azure SDK dependencies for Key Vault and OpenAI integration

### 📈 Performance Improvements

- **Caching Strategy**: Intelligent audio segment caching reduces API calls
- **Async Operations**: Non-blocking I/O for better performance
- **Rate Limiting**: Exponential backoff for Azure API calls
- **Memory Optimization**: Stream large audio files to reduce memory usage

---

## [1.0.0] - 2024-Initial

### ✨ Initial Release

#### 🎙️ Core Features
- **Microsoft Learn Integration**: Fetch content from Microsoft Learn modules
- **Text-to-Speech**: Azure Speech Services integration
- **Web Interface**: Flask-based web application
- **CLI Tool**: Command-line interface for batch processing
- **Multi-Voice Support**: Basic Sarah and Mike voice configuration

#### 🏗️ Architecture
- **Modular Design**: Separated content fetching, processing, and audio generation
- **Cache System**: Basic audio caching for performance
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Environment variable-based configuration

#### 🚀 Deployment
- **Docker Support**: Containerized application with Docker
- **Azure Integration**: Basic Azure container deployment
- **Environment Configuration**: Development and production environments
