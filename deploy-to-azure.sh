#!/bin/bash
# Azure Container Apps Deployment Script for EdutainmentForge
# This script follows Azure best practices for secure deployment

set -e

# Configuration
RESOURCE_GROUP="rg-edutainmentforge"
LOCATION="eastus2"
NAME_PREFIX="edutainmentforge"
CONTAINER_IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Azure Container Apps deployment for EdutainmentForge${NC}"

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged into Azure
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged into Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}📋 Using subscription: $SUBSCRIPTION_ID${NC}"

# Prompt for Azure Speech Service key
echo -e "${YELLOW}🔑 Please enter your Azure Speech Service key:${NC}"
read -s AZURE_SPEECH_KEY
echo

if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo -e "${RED}❌ Azure Speech Service key is required${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Step 1: Creating resource group${NC}"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

echo -e "${GREEN}🏗️  Step 2: Deploying infrastructure with Bicep${NC}"
DEPLOYMENT_NAME="edutainmentforge-$(date +%Y%m%d-%H%M%S)"

# Get the container registry name that will be created
ACR_NAME="${NAME_PREFIX}acr$(echo $SUBSCRIPTION_ID$RESOURCE_GROUP | sha256sum | cut -c1-10)"

DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file azure-infrastructure.bicep \
    --parameters \
        namePrefix=$NAME_PREFIX \
        azureSpeechKey="$AZURE_SPEECH_KEY" \
        azureSpeechRegion=$LOCATION \
        containerImage="$ACR_NAME.azurecr.io/edutainmentforge:$CONTAINER_IMAGE_TAG" \
    --name $DEPLOYMENT_NAME \
    --output json)

# Extract outputs
CONTAINER_REGISTRY_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.containerRegistryName.value')
CONTAINER_REGISTRY_LOGIN_SERVER=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.containerRegistryLoginServer.value')
CONTAINER_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.containerAppUrl.value')

echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
echo -e "${GREEN}📝 Container Registry: $CONTAINER_REGISTRY_NAME${NC}"
echo -e "${GREEN}🌐 App URL: $CONTAINER_APP_URL${NC}"

echo -e "${GREEN}🐳 Step 3: Building and pushing container image${NC}"

# Build the Docker image
echo "Building Docker image..."
docker build -t edutainmentforge:$CONTAINER_IMAGE_TAG .

# Tag for ACR
docker tag edutainmentforge:$CONTAINER_IMAGE_TAG $CONTAINER_REGISTRY_LOGIN_SERVER/edutainmentforge:$CONTAINER_IMAGE_TAG

# Login to ACR and push
echo "Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY_NAME

echo "Pushing image to ACR..."
docker push $CONTAINER_REGISTRY_LOGIN_SERVER/edutainmentforge:$CONTAINER_IMAGE_TAG

echo -e "${GREEN}🔄 Step 4: Updating container app with new image${NC}"
az containerapp update \
    --name "${NAME_PREFIX}-app" \
    --resource-group $RESOURCE_GROUP \
    --image $CONTAINER_REGISTRY_LOGIN_SERVER/edutainmentforge:$CONTAINER_IMAGE_TAG

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your EdutainmentForge app is available at: $CONTAINER_APP_URL${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo -e "   Resource Group: $RESOURCE_GROUP"
echo -e "   Container Registry: $CONTAINER_REGISTRY_NAME"
echo -e "   App URL: $CONTAINER_APP_URL"
echo -e "   Location: $LOCATION"
echo ""
echo -e "${GREEN}🎉 Happy podcasting!${NC}"
