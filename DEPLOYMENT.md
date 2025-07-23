# Azure Container Apps Deployment Guide for EdutainmentForge

## Overview
This guide shows how to deploy the updated EdutainmentForge application with the new "Discover Content" and "Podcast Library" features to Azure Container Apps.

## Prerequisites
- Azure CLI installed and logged in (`az login`)
- Docker installed
- Access to the existing Azure resources:
  - Resource Group: `edutainmentforge-rg`
  - Container Registry: `edutainmentforge.azurecr.io`
  - Container App: `edutainmentforge-app`

## Quick Deployment Steps

### Option 1: Using the Quick Deploy Script
```bash
# Navigate to the project directory
cd /path/to/EdutainmentForge

# Run the quick deployment script
./scripts/quick-deploy.sh
```

### Option 2: Manual Deployment
```bash
# 1. Set subscription (if needed)
az account set --subscription e440a65b-7418-4865-9821-88e411ffdd5b

# 2. Build and push to Azure Container Registry
az acr build \
  --registry edutainmentforge \
  --image edutainmentforge:latest \
  --file Dockerfile \
  .

# 3. Update Container App
az containerapp update \
  --name edutainmentforge-app \
  --resource-group edutainmentforge-rg \
  --image edutainmentforge.azurecr.io/edutainmentforge:latest
```

### Option 3: Docker-based Deployment
```bash
# Run the full deployment script
./scripts/deploy-container-to-azure.sh
```

## What Gets Deployed
The deployment includes:
- ✅ Fixed navigation with all tabs: "Create Podcast", "Discover Content", "Podcast Library" 
- ✅ Microsoft Learn Catalog API integration for content discovery
- ✅ Advanced search and filtering capabilities
- ✅ Learning path batch processing
- ✅ Enhanced podcast library management
- ✅ All existing authentication and TTS features

## Verification Steps
After deployment, verify the application at:
https://edutainmentforge-app.happymeadow-088e7533.eastus.azurecontainerapps.io/

You should see:
1. Complete navigation bar with all 4 tabs
2. "Discover Content" tab with search and filtering
3. "Podcast Library" tab with management features
4. Proper authentication flow

## Troubleshooting
- If deployment fails, check Azure CLI authentication: `az account show`
- Verify container registry access: `az acr list`
- Check container app status: `az containerapp show --name edutainmentforge-app --resource-group edutainmentforge-rg`

## Support
For issues, check the Azure portal logs or contact the development team.