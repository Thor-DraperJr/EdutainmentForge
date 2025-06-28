#!/bin/bash

# EdutainmentForge Azure Deployment Script
# This script deploys the application to Azure Container Apps in the existing edutainmentforge-rg resource group

set -e

# Configuration
RESOURCE_GROUP="edutainmentforge-rg"
LOCATION="eastus2"
ACR_NAME="edutainmentforge"
CONTAINER_APP_NAME="edutainmentforge-app"
ENVIRONMENT_NAME="edutainmentforge-env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting EdutainmentForge Azure deployment...${NC}"

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please log in...${NC}"
    az login
fi

# Check if resource group exists
echo -e "${YELLOW}📋 Checking if resource group exists...${NC}"
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${RED}❌ Resource group '$RESOURCE_GROUP' not found!${NC}"
    echo -e "${YELLOW}   Please make sure you have access to the existing resource group.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Resource group '$RESOURCE_GROUP' found!${NC}"

# Prompt for Azure Speech Service key
echo -e "${YELLOW}🔑 Please enter your Azure Speech Service key:${NC}"
read -s AZURE_SPEECH_KEY

if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo -e "${RED}❌ Azure Speech Service key is required!${NC}"
    exit 1
fi

# Build and push Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
docker build -t edutainmentforge:latest .

# Check if ACR exists, create if not
echo -e "${YELLOW}📦 Checking Azure Container Registry...${NC}"
if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${YELLOW}📦 Creating Azure Container Registry...${NC}"
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true \
        --location "$LOCATION"
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer --output tsv)

# Login to ACR
echo -e "${YELLOW}🔐 Logging in to Azure Container Registry...${NC}"
az acr login --name "$ACR_NAME"

# Tag and push image
echo -e "${YELLOW}📤 Pushing image to Azure Container Registry...${NC}"
docker tag edutainmentforge:latest "$ACR_LOGIN_SERVER/edutainmentforge:latest"
docker push "$ACR_LOGIN_SERVER/edutainmentforge:latest"

# Deploy using Bicep
echo -e "${YELLOW}☁️  Deploying to Azure Container Apps...${NC}"
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file deploy/main.bicep \
    --parameters \
        location="$LOCATION" \
        environmentName="$ENVIRONMENT_NAME" \
        containerAppName="$CONTAINER_APP_NAME" \
        acrName="$ACR_NAME" \
        azureSpeechKey="$AZURE_SPEECH_KEY"

# Get the application URL
echo -e "${YELLOW}🔍 Getting application URL...${NC}"
APP_URL=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query properties.outputs.containerAppUrl.value \
    --output tsv)

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Application URL: $APP_URL${NC}"
echo -e "${YELLOW}📝 It may take a few minutes for the application to be fully available.${NC}"

# Show logs command
echo -e "${YELLOW}📊 To view logs, use:${NC}"
echo "az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
