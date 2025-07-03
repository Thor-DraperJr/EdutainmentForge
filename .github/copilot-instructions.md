# GitHub Copilot Instructions for EdutainmentForge

## Project Context

EdutainmentForge is a Python-based web application that transforms Microsoft Learn technical content into engaging educational podcasts using AI-enhanced multi-voice narration. The project uses Flask for the web interface and relies on Azure services including Azure OpenAI (gpt-4o-mini), Azure Speech, and Container Apps for deployment.

### Current Status
- Core functionality is working: content scraping, AI enhancement, and audio generation
- Basic Flask web UI is implemented and deployed to Azure Container Apps
- Current focus is adding user authentication via Microsoft Entra ID (Azure AD B2C)

### Authentication Requirements
- Need to implement email-based registration for all users before they can access the app
- Support both Microsoft organizational accounts and personal accounts (outlook.com, etc.)
- Admin should be able to control the number of users and revoke access
- This will be used for a hackathon, so authentication should be simple but secure
- Prefer Azure-native solutions that integrate well with existing infrastructure

### Technical Environment
- Python 3.8+ Flask application
- Azure Container Apps for hosting
- Azure Key Vault for secret management
- All infrastructure defined and deployed through Azure CLI or Bicep
- Testing done in WSL environment before deployment

### Current Priorities
1. Implement and test Microsoft Entra ID B2C authentication
2. Ensure it works with both organizational and personal accounts
3. Deploy the updated application to Azure
4. Document the authentication flow for users

### Key Challenges
- Need to balance security with ease of use for hackathon participants
- Must maintain clean separation between auth code and business logic
- Environment variables must be consistent between local and Azure deployments

## Azure Infrastructure Reference

**IMPORTANT**: Always use the MCP server to reference and validate the existing Azure infrastructure before making changes.

### Dynamic Infrastructure Discovery
Use MCP server to discover current environment for accuracy and flexibility:

```bash
# Get current subscription details
mcp_azure_mcp_ser_azmcp-subscription-list

# List available resource groups  
mcp_azure_mcp_ser_azmcp-group-list

# Get specific resource group resources
mcp_azure_mcp_ser_azmcp-extension-az --command "resource list --resource-group [RESOURCE_GROUP_NAME]"
```

### Expected Resource Pattern
The project expects to find these resource types:
- **Azure OpenAI**: For AI script enhancement with gpt-4o-mini deployment
- **Azure Speech**: For text-to-speech services
- **Key Vault**: For secure secret management  
- **Container Apps Environment**: For deployment
- **Container Registry**: For container images
- **Storage Account**: For file storage
- **Log Analytics**: For monitoring and logging

### Security Best Practices
- **Never hardcode** API keys, passwords, or connection strings in code or documentation
- **Protect sensitive IDs** - subscription IDs and tenant IDs should not be exposed in public repos
- **Validate permissions** before attempting resource operations
- **Use least privilege** access patterns
- **Audit all operations** through proper logging

### MCP Server Usage Guidelines
When working with Azure resources, always use the MCP server to:
1. **Validate current state** - ensure resources exist and are accessible
2. **Get accurate configurations** - retrieve current deployments and settings
3. **Check service availability** before making configuration changes
4. **Verify deployments and endpoints** for reliability
5. **Manage Key Vault secrets** securely
6. **Follow security best practices** - validate permissions and audit operations

## Coding Standards

- **Language**: Python 3.8+
- **Style**: Follow PEP 8 strictly
- **Naming**: Use snake_case for functions/variables, PascalCase for classes
- **Documentation**: Include docstrings for all public functions
- **Error Handling**: Use proper exception handling with specific exception types

## Architecture Patterns

- Separate content fetching, audio processing, and UI logic
- Use dependency injection for external services
- Implement proper logging throughout the application
- Follow the established folder structure in src/
- Cache audio segments for performance
- Support both single and multi-voice TTS

## Security Requirements

- **Never hardcode API keys or secrets** - these provide access to resources
- Always load credentials from environment variables or Key Vault
- Validate and sanitize all user inputs
- Use secure HTTP libraries (requests with SSL verification)
- Support Azure Key Vault for production secrets
- Use Azure Managed Identity when possible
- **MCP Server Integration**: Use MCP tools to validate Azure resources and manage secrets securely

## Configuration Management Pattern

**IMPORTANT**: Follow consistent configuration management across environments:

### Local Development Environment
- **API Keys**: Load from `.env` file (for development only)
- **Voice Configuration**: Load from `.env` file
- **Other Settings**: Load from `.env` file
- **Example**: `SARAH_VOICE=en-US-EmmaNeural` in `.env`

### Azure Production Environment  
- **API Keys**: Load from Azure Key Vault secrets via managed identity
- **Voice Configuration**: Load from Azure Key Vault secrets via managed identity
- **Other Settings**: Environment variables (non-sensitive values only)
- **Example**: `SARAH_VOICE` environment variable references `sarah-voice` Key Vault secret

### Key Vault Secret Naming Convention
- `azure-speech-key` - Azure Speech API key
- `azure-openai-api-key` - Azure OpenAI API key
- `azure-openai-endpoint` - Azure OpenAI endpoint URL
- `sarah-voice` - Sarah's voice identifier (e.g., "en-US-EmmaNeural")
- `mike-voice` - Mike's voice identifier (e.g., "en-US-DavisNeural")
- `azure-ad-b2c-tenant-id` - Azure AD B2C tenant ID
- `azure-ad-b2c-client-id` - Azure AD B2C application client ID
- `azure-ad-b2c-client-secret` - Azure AD B2C application client secret
- `azure-ad-b2c-policy-name` - Azure AD B2C user flow policy name
- `flask-secret-key` - Flask session secret key

### Configuration Best Practices
1. **Single Source of Truth**: Each environment has one source for each config value
2. **No Hardcoded Values**: Never hardcode voice names or API keys in YAML/code
3. **Environment Parity**: Local `.env` structure mirrors Azure Key Vault secrets
4. **Secure by Default**: All sensitive config comes from secure sources
5. **Easy Updates**: Change voices by updating Key Vault, not redeploying code

## Required Libraries & Dependencies

### Core Dependencies
- **HTTP Requests**: `requests>=2.31.0` for web scraping
- **HTML Parsing**: `beautifulsoup4>=4.12.0` for content extraction
- **Environment Config**: `python-dotenv>=1.0.0` for .env file support
- **Web Framework**: `flask>=3.0.0` for UI and APIs
- **Audio Processing**: `pydub>=0.25.1` for audio manipulation
- **Production Server**: `gunicorn>=21.2.0` for deployment

### Azure Services
- **Azure Speech**: `azure-cognitiveservices-speech>=1.34.0` for TTS
  - **Service**: `edutainmentforge-speech` (eastus2)
- **Azure OpenAI**: `openai>=1.12.0` for AI script enhancement
  - **Service**: `edutainmentforge-openai` (eastus2)
  - **Deployed Model**: `gpt-4o-mini`
- **Azure Key Vault**: For secure secret management
  - **Service**: `edutainmentforge-kv` (eastus)
- **Azure AD B2C**: `msal>=1.24.0` and `Flask-Session>=0.5.0` for authentication
  - **Service**: Azure AD B2C tenant for user management
- **TTS Fallback**: `pyttsx3>=2.90` for local development

### Testing Dependencies
- **Test Framework**: `pytest>=7.4.0` for unit tests
- **Mocking**: `pytest-mock>=3.11.0` for test mocking

### Standard Library Modules (No Installation Required)
- **pathlib** - Modern path handling
- **threading** - Background processing for web interface
- **uuid** - Unique ID generation for tracking
- **argparse** - Command-line argument parsing
- **tempfile** - Temporary file management for audio processing
- **json** - Data serialization and API responses
- **re** - Regular expressions for text processing and dialogue parsing
- **hashlib** - Content hashing for caching
- **urllib.parse** - URL parsing and manipulation
- **abc** - Abstract base classes for service interfaces
- **io** - Binary stream handling for audio files
- **os** - Operating system interface
- **sys** - System-specific parameters
- **time** - Time-related functions

## Code Generation Guidelines

When generating code:
1. Include proper error handling and logging
2. Add type hints where appropriate
3. Write accompanying unit tests
4. Use our established utility functions
5. Follow the single responsibility principle
6. Support both AI-enhanced and basic dialogue modes
7. Implement proper voice mapping for multi-speaker TTS
8. **Resource Management**: Always use context managers for file operations
9. **Error Recovery**: Implement graceful degradation for service failures
10. **Rate Limiting**: Respect Azure service rate limits and implement backoff
11. **Configuration Consistency**: Use the same config pattern (env vars/Key Vault) for all environment-specific values

## Configuration Management Rules

**CRITICAL**: Maintain consistency between local and Azure environments:

1. **Never hardcode configuration** in source code (voices, endpoints, etc.)
2. **Mirror structure**: Local `.env` should mirror Azure Key Vault secrets
3. **Same variable names**: Use identical environment variable names across environments
4. **Secure by default**: Treat all environment-specific config as potentially sensitive
5. **Single source per environment**: One authoritative source for each config value per environment

### Example Configuration Patterns
```python
# ✅ CORRECT: Load from environment
voice_config = {
    'sarah_voice': os.getenv('SARAH_VOICE', 'en-US-EmmaNeural'),
    'mike_voice': os.getenv('MIKE_VOICE', 'en-US-DavisNeural')
}

# ❌ WRONG: Hardcoded values
voice_config = {
    'sarah_voice': 'en-US-AriaNeural',  # Hardcoded!
    'mike_voice': 'en-US-DavisNeural'
}
```

## Testing Expectations

- Generate unit tests for all new functions
- Include edge cases and error conditions
- Use descriptive test names that explain the scenario
- Mock external dependencies appropriately
- **Test Cleanup**: Always clean up resources and temporary files after tests
- **Azure Resource Testing**: Use test-specific resource groups or mock Azure services
- **Audio File Cleanup**: Remove generated audio files in test teardown
- **Cache Cleanup**: Clear test caches to avoid interference between tests

## Test Cleanup Guidelines

### Required Cleanup Patterns
```python
import tempfile
import pytest
from pathlib import Path

class TestAudioGeneration:
    def setup_method(self):
        """Setup test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def teardown_method(self):
        """Clean up after each test"""
        # Clean up temporary audio files
        for file_path in self.test_files:
            if Path(file_path).exists():
                Path(file_path).unlink()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear cache if used
        from src.utils.cache import clear_test_cache
        clear_test_cache()
```

### Azure Service Testing
- **Never use production resources** in automated tests
- **Mock Azure services** using pytest-mock or similar
- **Use test doubles** for expensive operations (TTS, AI enhancement)
- **Environment isolation** - use separate test configurations

### File System Testing
- **Use tempfile.mkdtemp()** for temporary directories
- **Track all created files** in test setup
- **Clean up in teardown** even if tests fail
- **Test audio cache cleanup** to prevent disk space issues

## MCP Server Integration Guidelines

When working with Azure resources, always use the MCP server to:

### Resource Validation
```bash
# Example MCP server calls to validate infrastructure
mcp_azure_mcp_ser_azmcp-group-list  # List resource groups
mcp_azure_mcp_ser_azmcp-extension-az  # Run Azure CLI commands
```

### Key Vault Operations
```bash
# Check Key Vault secrets
mcp_azure_mcp_ser_azmcp-keyvault-secret-get
# Set Key Vault secrets  
mcp_azure_mcp_ser_azmcp-keyvault-secret-set
```

### Azure OpenAI Validation
```bash
# Verify Azure OpenAI deployments
mcp_azure_mcp_ser_azmcp-extension-az --command "cognitiveservices account deployment list"
```

### Before Making Infrastructure Changes
1. **Always** query current state using MCP server
2. Verify resource names and locations match expected patterns
3. Check service availability and deployment status
4. Validate permissions and access before proceeding

## Example Code Style

```python
def fetch_learn_content(module_id: str) -> dict:
    """
    Fetch content from Microsoft Learn module.
    
    Args:
        module_id: The MS Learn module identifier
        
    Returns:
        Dictionary containing module content
        
    Raises:
        ContentFetchError: If content cannot be retrieved
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Failed to fetch content for module {module_id}: {e}")
        raise ContentFetchError(f"Content fetch failed: {e}")
```

## AI Enhancement Guidelines

When working with the AI script enhancement feature:
- Always provide fallbacks when Azure OpenAI is unavailable
- Ensure enhanced scripts maintain proper dialogue format
- Balance conversation between Sarah and Mike (50/50 split)
- Handle table content with special dialogue enhancements
- Log all AI interactions for debugging
- Monitor token usage through Azure Portal for cost optimization

## Multi-Voice TTS Guidelines

- Use distinct premium voices for each speaker (Sarah: EmmaNeural, Mike: DavisNeural)
- Parse dialogue scripts with proper speaker identification
- Add appropriate pauses between speaker segments
- Cache TTS service instances to avoid recreation
- Support fallback to single voice if multi-voice fails
- **Voice Configuration**: Load voice names from environment variables/Key Vault, never hardcode
- **Current Voices**: Emma (en-US-EmmaNeural) for Sarah, Davis (en-US-DavisNeural) for Mike
- Use descriptive test names that explain the scenario
- Mock external dependencies appropriately

## Azure AD B2C Authentication Guidelines

### Implementation Requirements
- **Authentication Flow**: Use MSAL Python library with PKCE for secure authentication
- **User Experience**: Seamless sign-up/sign-in with both Microsoft accounts and external accounts
- **Session Management**: Use Flask-Session for secure session handling
- **Route Protection**: Implement decorators to protect routes requiring authentication

### Azure AD B2C Configuration
- **Tenant Setup**: Create dedicated B2C tenant for user management
- **User Flows**: Configure sign-up/sign-in policies with customizable user experience
- **App Registration**: Register Flask application with proper redirect URIs and permissions
- **Multi-Account Support**: Enable both organizational (Azure AD) and personal (MSA) accounts

### Security Best Practices
- **Token Validation**: Properly validate ID tokens and access tokens
- **Session Security**: Use secure session cookies with appropriate expiration
- **CSRF Protection**: Implement CSRF protection for authentication flows
- **Error Handling**: Graceful error handling for authentication failures

### Development Workflow
1. **Local Testing**: Use Azure AD B2C development tenant for local testing
2. **Environment Consistency**: Maintain consistent configuration between local and production
3. **Secret Management**: Store all B2C configuration in Azure Key Vault
4. **Testing**: Implement comprehensive tests for authentication flows

## Performance & Optimization Guidelines

- **Caching Strategy**: Cache audio segments by content hash to avoid regeneration
- **Async Operations**: Use async/await for I/O-bound operations (API calls, file operations)
- **Rate Limiting**: Implement exponential backoff for Azure API calls
- **Memory Management**: Stream large audio files instead of loading entirely in memory
- **Error Recovery**: Implement circuit breaker pattern for external service failures
- **Monitoring**: Log performance metrics and Azure service usage

## Deployment & Troubleshooting

### Local Development Setup
1. Use MCP server to validate Azure resources are accessible
2. Set up `.env` file with required API keys and voice configuration (mirrors Key Vault structure)
3. Install dependencies: `pip install -r requirements.txt`
4. Test configuration: Run validation scripts before development

### Azure Production Configuration
1. All secrets stored in Azure Key Vault (API keys AND voice configuration)
2. Container App uses managed identity to access Key Vault secrets
3. Environment variables reference secrets via `secretRef` in azure-container-app.yaml
4. Voice updates require only Key Vault secret changes, not container redeployment

### Common Issues & Solutions
- **Azure API Rate Limits**: Implement exponential backoff and request queuing
- **Audio Generation Failures**: Always have fallback TTS options available  
- **Key Vault Access Issues**: Verify Azure CLI authentication and permissions
- **Container Deployment**: Ensure proper secret mounting and environment variables
- **Memory Issues**: Stream large files and clean up temporary audio files
