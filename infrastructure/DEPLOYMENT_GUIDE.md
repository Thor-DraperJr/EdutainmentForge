# Infrastructure Deployment Guide

This guide provides a streamlined approach to deploying EdutainmentForge to Azure using modern RBAC-based security practices.

## Overview

The infrastructure consists of:
- **Container Apps Environment**: Hosting the web application with system-assigned managed identity
- **Key Vault**: RBAC-enabled secure secret management with network restrictions
- **Storage Account**: File storage for audio cache and temporary files
- **Container Registry**: Private container image storage
- **Log Analytics**: Application monitoring and logging

## Security Architecture

### 🔐 **Modern RBAC Authentication**
- **Key Vault**: RBAC-enabled (not legacy access policies)
- **Network Security**: Network-restricted Key Vault (deny public access)
- **Identity**: System-assigned managed identity (automatically managed service principal)
- **Permissions**: Minimal permissions with "Key Vault Secrets User" role (read-only)

### 🛡️ **Security Features**
1. **System-Assigned Managed Identity**: Automatically managed, no credential rotation needed
2. **RBAC Authorization**: Modern, granular permission model
3. **Network-Restricted Key Vault**: Enhanced security with Azure service bypass
4. **Minimal Permissions**: Read-only secret access, no administrative rights
5. **Private Container Registry**: Secure image storage with managed identity access

## Prerequisites

1. **Azure CLI** installed and logged in: `az login`
2. **Docker** installed for building container images
3. **Azure subscription** with appropriate permissions

## Deployment Process

### 1. Create Resource Group

```bash
# Set your preferred location
LOCATION="eastus2"
RESOURCE_GROUP="edutainmentforge-rg"

az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 2. Deploy Infrastructure

```bash
# Deploy using the clean Bicep template
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infrastructure/azure-infrastructure-clean.bicep \
  --parameters location=$LOCATION
```

### 3. Set Up Secrets

```bash
# Run the interactive secret setup script
./infrastructure/setup-secrets.sh
```

This script will prompt you for:
- Azure Speech Service key
- Azure OpenAI API key and endpoint
- Azure AD B2C configuration
- Voice preferences (defaults to Emma/Davis)

### 4. Build and Deploy Container

Use Docker or your CI pipeline (GitHub Action already handles deploys on main pushes):

```bash
# Build locally (optional if CI handles builds)
docker build -t edutainmentforge:latest .

# Tag & push (only if you manually push images)
az acr login --name edutainmentforge
docker tag edutainmentforge:latest edutainmentforge.azurecr.io/edutainmentforge:latest
docker push edutainmentforge.azurecr.io/edutainmentforge:latest
```

The GitHub Actions workflow (`.github/workflows/deploy.yml`) will build and deploy automatically when changes are pushed to `main`.

## Configuration Details

### RBAC Role Assignments

The deployment automatically assigns these roles to the container app's managed identity:

| Role | Scope | Purpose |
|------|-------|---------|
| `Key Vault Secrets User` | Key Vault | Read-only access to secrets |
| `AcrPull` | Container Registry | Pull container images |

### Key Vault Secrets

All secrets are managed in Azure Key Vault with RBAC authorization:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `azure-speech-key` | Azure Speech Service API key | `a1b2c3d4e5f6...` |
| `azure-openai-api-key` | Azure OpenAI API key | `sk-abcd1234...` |
| `azure-openai-endpoint` | Azure OpenAI endpoint URL | `https://your-openai.openai.azure.com/` |
| `sarah-voice` | Sarah's TTS voice identifier | `en-US-EmmaNeural` |
| `mike-voice` | Mike's TTS voice identifier | `en-US-DavisNeural` |
| `flask-secret-key` | Flask session secret (auto-generated) | `base64-encoded-key` |
| `azure-ad-b2c-tenant-id` | B2C tenant ID | `yourtenant.onmicrosoft.com` |
| `azure-ad-b2c-client-id` | B2C application client ID | `12345678-1234-1234-1234-123456789012` |
| `azure-ad-b2c-client-secret` | B2C application secret | `client-secret-value` |
| `azure-ad-b2c-policy-name` | B2C user flow policy | `B2C_1_signupsignin` |

### Secret Management Permissions

To manage secrets, you need one of these roles on the Key Vault:
- `Key Vault Secrets Officer` (recommended): Full secret management
- `Key Vault Administrator`: Full Key Vault management
- `Owner` or `Contributor`: Azure resource management

The container app only has `Key Vault Secrets User` (read-only) for security.

### Environment Variables

The container app receives configuration through environment variables that reference Key Vault secrets:

```yaml
env:
  - name: AZURE_SPEECH_KEY
    secretRef: azure-speech-key
  - name: SARAH_VOICE
    secretRef: sarah-voice
  # ... other variables
```

## Security Features

1. **System-Assigned Managed Identity**: Container app uses automatically managed service principal for Key Vault access
2. **RBAC Authorization**: Modern role-based access control instead of legacy access policies
3. **Network-Restricted Key Vault**: Public access denied, Azure services bypass enabled
4. **HTTPS Only**: Container app configured for HTTPS traffic only
5. **Minimal Permissions**: Container app has only necessary read permissions (Key Vault Secrets User)
6. **Private Registry**: Container images stored in private Azure Container Registry

### RBAC vs Legacy Access Policies

This deployment uses **RBAC authorization** which provides:
- ✅ Granular, role-based permissions
- ✅ Integration with Azure AD identity management
- ✅ Audit trail through Azure Activity Log
- ✅ Consistent permission model across Azure services
- ❌ Legacy access policies are not used (deprecated approach)

## Monitoring

- **Application Logs**: Available in Log Analytics workspace
- **Container Metrics**: CPU, memory, and request metrics in Azure Monitor
- **Key Vault Access**: Audit logs for secret access

## Updating Configuration

### Update Voice Configuration

```bash
# Change Sarah's voice
az keyvault secret set --vault-name edutainmentforge-kv --name sarah-voice --value "en-US-AriaNeural"

# Container app will automatically pick up the change
```

### Update API Keys

```bash
# Update Azure Speech key
az keyvault secret set --vault-name edutainmentforge-kv --name azure-speech-key --value "new-key-value"
```

### Deploy New Application Version

Automatic on push to `main` via CI. To force a manual image update:

```bash
docker build -t edutainmentforge:latest .
az acr login --name edutainmentforge
docker tag edutainmentforge:latest edutainmentforge.azurecr.io/edutainmentforge:latest
docker push edutainmentforge.azurecr.io/edutainmentforge:latest
az containerapp update \
  --name edutainmentforge-app \
  --resource-group edutainmentforge-rg \
  --image edutainmentforge.azurecr.io/edutainmentforge:latest
```

## Troubleshooting

### Check Container App Status

```bash
az containerapp show --name edutainmentforge-app --resource-group edutainmentforge-rg --query "properties.runningStatus"
```

### View Application Logs

```bash
az containerapp logs show --name edutainmentforge-app --resource-group edutainmentforge-rg --follow
```

### Verify RBAC Permissions

```bash
# Check role assignments for the container app
az role assignment list --all --query "[?contains(scope, 'edutainmentforge-kv')].{Principal:principalId, Role:roleDefinitionName, Type:principalType}" -o table

# Verify Key Vault RBAC is enabled
az keyvault show --name edutainmentforge-kv --query "properties.enableRbacAuthorization"
```

### Test Key Vault Access from Container App

```bash
# Get container app's managed identity
PRINCIPAL_ID=$(az containerapp show --name edutainmentforge-app --resource-group edutainmentforge-rg --query "identity.principalId" -o tsv)

# Check if it has the correct role
az role assignment list --assignee $PRINCIPAL_ID --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/edutainmentforge-rg/providers/Microsoft.KeyVault/vaults/edutainmentforge-kv
```

### Common Issues

1. **Key Vault Access Denied**:
   - Ensure RBAC is enabled: `"enableRbacAuthorization": true`
   - Verify container app has "Key Vault Secrets User" role
   - Check network access rules if using network restrictions

2. **Container Won't Start**:
   - Check that all required secrets exist in Key Vault
   - Verify secret references match exact secret names
   - Ensure system-assigned identity is enabled

3. **Secret Not Found**:
   - Verify secret name matches exactly (case-sensitive)
   - Check that you have sufficient permissions to create secrets
   - Ensure Key Vault name is correct in bicep template

## Migration from Old Infrastructure

If you have existing infrastructure with hardcoded values:

1. **Extract Current Configuration**: Note your current API keys and settings
2. **Deploy New Infrastructure**: Use `azure-infrastructure-clean.bicep`
3. **Set Secrets**: Use `setup-secrets.sh` with your existing values
4. **Test Deployment**: Verify everything works with the new setup
5. **Clean Up Old Resources**: Remove old infrastructure after verification

## Cost Optimization

- **Container Apps**: Scales to zero when not in use
- **Storage**: Standard LRS for cost-effective file storage
- **Key Vault**: Standard tier for secrets management
- **Log Analytics**: 30-day retention to control costs

Estimated monthly cost for light usage: $20-50 USD

## Security Best Practices

1. **Regular Key Rotation**: Rotate API keys every 90 days
2. **Monitor Access**: Review Key Vault access logs regularly
3. **Least Privilege**: Only grant necessary permissions
4. **Environment Separation**: Use separate Key Vaults for dev/prod
5. **Backup Secrets**: Export and securely store secret values
