# EdutainmentForge - Copilot Instructions

## Project Overview
Python Flask app that converts Microsoft Learn content into AI-enhanced educational podcasts using Azure OpenAI (gpt-4o-mini) and Azure Speech Services.

**Current Priority**: Implement Azure AD B2C authentication for hackathon deployment.

## Tech Stack
- **Backend**: Python 3.8+, Flask
- **Infrastructure**: Azure Container Apps, Key Vault, Bicep
- **AI Services**: Azure OpenAI (gpt-4o-mini), Azure Speech
- **Auth**: Azure AD B2C (planned)

## Key Rules

### Security
- Never hardcode secrets - use environment variables or Key Vault
- Load config: Local `.env` → Production Key Vault secrets
- Use MCP server tools for Azure resource validation

### Configuration Pattern
```python
# ✅ Correct
voice = os.getenv('SARAH_VOICE', 'en-US-EmmaNeural')

# ❌ Wrong  
voice = 'en-US-AriaNeural'  # Hardcoded!
```

### Code Standards
- Follow PEP 8, snake_case functions, PascalCase classes
- Include docstrings, type hints, error handling
- Write tests with proper cleanup (tempfile, mock Azure services)
- Use context managers for file operations

### Azure Integration
- Always use MCP server to validate resources before changes
- When connecting to Key Vault use a service principal
- Key Vault secrets: `azure-speech-key`, `azure-openai-api-key`, `sarah-voice`, `mike-voice`
- Container Apps: Managed identity access to Key Vault and ACR

### Authentication Requirements (Next Sprint)
- Azure AD B2C with MSAL Python
- Support Microsoft + personal accounts  
- Email-based registration with admin controls
- Flask-Session for secure session management

## Architecture
- `src/content/` - Microsoft Learn API integration
- `src/audio/` - TTS with multi-voice support (Sarah: Emma, Mike: Davis)
- `src/utils/` - Caching, config management
- `infrastructure/` - Bicep templates with RBAC security