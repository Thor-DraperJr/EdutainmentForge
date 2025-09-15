#  Project Overview
Python Flask app that converts Microsoft Learn content into AI-enhanced educational podcasts using Azure OpenAI (gpt-4o-mini) and Azure Speech Services. This is for the Hackathon 2025 challenge, so we don't need to use robust production practices, but we should follow best practices for security, code quality, and Azure integration.

## Copilot Instructions
- Attempt to make environment changes with the Azure MCP server first.
- When troubleshooting, check the Microsoft Docs MCP server for best practices.
- Ensure all secrets are stored in Azure Key Vault and accessed via environment variables.

## Key Rules

### Security
- Never hardcode secrets - use environment variables or Key Vault
- Load config: Local `.env` → Production Key Vault secrets

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

# /new-session
Counduct a fresh analysis of the project, ignoring previous context. Give me a concise summary of the project purpose, architecture, and key components. Identify any potential improvements or optimizations.

## Prompt Command: /workflow-check

Goal: Quickly confirm CI workflow health and deployed commit without noise.

Usage: Ask: "/workflow-check".

Assistant Response Should Include:
1. Latest workflow run (branch main): status + conclusion + short SHA.
2. Simple follow-up commands (exactly three):
	 - List recent runs.
	 - Watch latest run until completion.
	 - View logs of latest run.
3. Reminder how to confirm deployed commit via app (`/prompt` version command).

Expected Output Template (example):
```
Latest Run: success (completed) commit=abc1234
Commands:
	gh run list --branch main --limit 3
	gh run watch $(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId')
	gh run view $(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId') --log
Verify Deploy:
	curl -s https://YOUR_HOST/healthz | jq .
	curl -s -X POST -H 'Content-Type: application/json' -d '{"command":"version"}' https://YOUR_HOST/prompt | jq .
```

Keep answers terse. Offer extended diagnostics only if the user explicitly asks for details.
