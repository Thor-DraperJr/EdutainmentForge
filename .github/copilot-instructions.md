#  Project Overview
Python Flask app that converts Microsoft Learn content into AI-enhanced educational podcasts using Azure OpenAI and Azure Speech Services. This is for the Hackathon 2025 challenge, so we don't need to use robust production practices, but we should follow best practices for security, code quality, and Azure integration. We don't need to worry about scaling or high availability, but we should be cost conscious.

There is no local development environment. The app itself is in a lab environment in Azure, and all changes should be made to the azure environment directly.

## Copilot Instructions
- Attempt to make environment changes with the Azure MCP server first.
- When asking for the name of an Azure resource, use the Azure MCP server.
- When troubleshooting, check the Microsoft Docs MCP server for best practices.
- Ensure all secrets are stored in Azure Key Vault and accessed via environment variables.

## Key Rules

### Security
- Never hardcode secrets - use environment variables or Key Vault
- Load config: Local `.env` → Prod

+uction Key Vault secrets

### Code Standards
- Follow PEP 8, snake_case functions, PascalCase classes
- Include docstrings, type hints, error handling
- Write tests with proper cleanup (tempfile, mock Azure services)
- Use context managers for file operations
- If a test script is created, conduct proper cleanup (either removing the test file or moving it to /scripts if it will be used again)

### Azure Integration
- When connecting to Key Vault use a service principal
- Key Vault secrets: `azure-speech-key`, `azure-openai-api-key`, `sarah-voice`, `mike-voice`
- Container Apps: Managed identity access to Key Vault and ACR

## Architecture
- `src/content/` - Microsoft Learn API integration
- `src/audio/` - TTS with multi-voice support (Sarah: Emma, Mike: Davis)
- `src/utils/` - Caching, config management
- `infrastructure/` - Bicep templates with RBAC security

## Prompt Commands

### /new-session
Goal: Conduct a fresh analysis of the project, ignoring previous context. Give me a concise summary of the project purpose, architecture, and key components. Also, print out the tree file structure in the terminal.

### /workflow-check

Goal: Quickly confirm CI workflow health and deployed commit without noise.

Assistant Response Should Include:
1. Latest workflow run (branch main): status + conclusion + short SHA.
2. Simple follow-up commands (exactly three):
	 - List recent runs.
	 - Watch latest run until completion.
	 - View logs of latest run.
