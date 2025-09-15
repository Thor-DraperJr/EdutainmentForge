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

## GitHub Actions / Workflow Health Quick Reference

Use these `gh` CLI commands after pushing to verify builds and deployments without running anything locally beyond the CLI itself.

### Core
```
gh workflow list
gh run list --limit 10
gh run list --branch main --limit 5
```

### Inspect latest run
```
RUN_ID=$(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId')
gh run view "$RUN_ID" --log
```

### Watch until completion
```
gh run watch $(gh run list --branch main --limit 1 --json databaseId -q '.[0].databaseId')
```

### JSON status snippet
```
gh run list --branch main --limit 1 --json status,conclusion,headSha -q '.[0]'
```

### Re-run most recent failed run (if any)
```
gh run list --branch main --limit 5 --json conclusion,databaseId -q '.[] | select(.conclusion=="failure") | .databaseId' | head -n1 | xargs -r gh run rerun
```

### Download artifacts
```
gh run download "$RUN_ID"
```

### Confirm deployed commit via app
```
curl -s https://YOUR_HOST/healthz | jq .
curl -s -X POST -H 'Content-Type: application/json' -d '{"command":"version"}' https://YOUR_HOST/prompt | jq .
```

### Helpful aliases (optional)
```
alias ghw='gh run list --limit 5'
alias ghwm='gh run list --branch main --limit 5'
```

Keep this lean; expand only if workflows grow more complex.