# GitHub Actions CI/CD Setup for EdutainmentForge

## Overview
This document explains how to set up automated deployment to Azure Container Apps using GitHub Actions.

## Prerequisites
- Azure CLI installed and logged in
- GitHub repository with admin access
- Azure Container Apps environment already deployed

## Setup Steps

### 1. Create Azure Service Principal
```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "edutainmentforge-github-actions" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/edutainmentforge-rg \
  --sdk-auth
```

Save the JSON output - you'll need it for step 2.

### 2. Configure GitHub Secrets
In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

- `AZURE_CREDENTIALS`: The entire JSON output from step 1

### 3. Workflow Features
The workflow (`.github/workflows/deploy.yml`) will:
- ✅ Trigger on pushes to main branch
- ✅ Allow manual deployment via workflow_dispatch
- ✅ Deploy source code directly to Azure Container Apps
- ✅ Show deployment URL in logs

### 4. Environment Variables
The workflow uses these environment variables:
- `AZURE_CONTAINERAPP_NAME`: edutainmentforge-app
- `AZURE_GROUP_NAME`: edutainmentforge-rg  
- `AZURE_CONTAINERAPP_ENV`: edutainmentforge-env

### 5. Security Features
- ✅ Uses Azure service principal with minimal required permissions
- ✅ Secrets stored securely in GitHub
- ✅ No hardcoded credentials in workflow files
- ✅ Scoped to specific resource group only

## Usage

### Automatic Deployment
- Push changes to main branch
- GitHub Actions will automatically deploy to Azure

### Manual Deployment  
- Go to Actions tab in GitHub
- Select "Deploy to Azure Container Apps" workflow
- Click "Run workflow"

## Monitoring
- Check Actions tab for deployment status
- View deployment logs for troubleshooting
- App URL is displayed in successful deployment logs

## Benefits vs Manual Deployment
- ✅ No local Docker required
- ✅ No manual secret handling
- ✅ Consistent deployment environment
- ✅ Deployment history and rollback capability
- ✅ Team collaboration friendly
- ✅ Automatically deploys latest changes
