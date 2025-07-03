#!/bin/bash

# EdutainmentForge - Non-Interactive Container Deployment Script
# This script builds and deploys the container using existing Azure infrastructure

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="edutainmentforge-rg"
APP_NAME="edutainmentforge-app"
CONTAINER_IMAGE_TAG="latest"

echo -e "${GREEN}🚀 EdutainmentForge Container Deployment${NC}"
echo "==========================================="

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
SUBSCRIPTION_ID=$(az account show --query id -o tsv | tr -d '\r\n')
echo -e "${GREEN}📋 Using subscription: $SUBSCRIPTION_ID${NC}"

echo -e "${GREEN}🔍 Step 1: Discovering existing infrastructure${NC}"

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}❌ Resource group '$RESOURCE_GROUP' not found.${NC}"
    echo -e "${YELLOW}Please ensure your infrastructure is deployed first.${NC}"
    exit 1
fi

# Get the container registry details from existing infrastructure
echo "Getting container registry details..."
CONTAINER_REGISTRY_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv | tr -d '\r\n' | xargs)
if [ -z "$CONTAINER_REGISTRY_NAME" ]; then
    echo -e "${RED}❌ No container registry found in resource group '$RESOURCE_GROUP'${NC}"
    exit 1
fi

CONTAINER_REGISTRY_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP --query "loginServer" -o tsv | tr -d '\r\n' | xargs)

# Debug output to check for hidden characters
echo "Debug: Registry name length: ${#CONTAINER_REGISTRY_NAME}"
echo "Debug: Login server length: ${#CONTAINER_REGISTRY_LOGIN_SERVER}"
echo "Debug: Login server hex dump: $(echo -n "$CONTAINER_REGISTRY_LOGIN_SERVER" | hexdump -C | head -1)"

echo -e "${GREEN}✅ Found container registry: $CONTAINER_REGISTRY_NAME${NC}"
echo -e "${GREEN}✅ Login server: $CONTAINER_REGISTRY_LOGIN_SERVER${NC}"

# Check if container app exists
if ! az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}❌ Container app '$APP_NAME' not found in resource group '$RESOURCE_GROUP'${NC}"
    echo -e "${YELLOW}Please ensure your container app is deployed first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found container app: $APP_NAME${NC}"

echo -e "${GREEN}🐳 Step 2: Building and pushing container image${NC}"

# Build the Docker image
echo "Building Docker image..."
docker build -t edutainmentforge:$CONTAINER_IMAGE_TAG .

# Create the full image name with proper escaping and sanitization
# Additional sanitization to remove any hidden characters
CLEAN_LOGIN_SERVER=$(echo "$CONTAINER_REGISTRY_LOGIN_SERVER" | tr -d '\r\n' | sed 's/[[:space:]]*$//' | sed 's/^[[:space:]]*//')
FULL_IMAGE_NAME="${CLEAN_LOGIN_SERVER}/edutainmentforge:${CONTAINER_IMAGE_TAG}"

echo "Debug: Clean login server: '$CLEAN_LOGIN_SERVER'"
echo "Debug: Full image name: '$FULL_IMAGE_NAME'"

# Tag for ACR
echo "Tagging image for ACR..."
docker tag edutainmentforge:$CONTAINER_IMAGE_TAG "$FULL_IMAGE_NAME"

# Login to ACR and push
echo "Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY_NAME

echo "Pushing image to ACR..."
docker push "$FULL_IMAGE_NAME"

echo -e "${GREEN}🔄 Step 3: Updating container app with new image${NC}"
az containerapp update \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image "$FULL_IMAGE_NAME"

# Get the app URL
CONTAINER_APP_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv | tr -d '\r\n')
if [ -n "$CONTAINER_APP_URL" ]; then
    CONTAINER_APP_URL="https://$CONTAINER_APP_URL"
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your EdutainmentForge app is available at: $CONTAINER_APP_URL${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo -e "   Resource Group: $RESOURCE_GROUP"
echo -e "   Container Registry: $CONTAINER_REGISTRY_NAME"
echo -e "   Container App: $APP_NAME"
echo -e "   Image: $FULL_IMAGE_NAME"
echo -e "   App URL: $CONTAINER_APP_URL"
echo ""
echo -e "${GREEN}🎉 Happy podcasting!${NC}"
