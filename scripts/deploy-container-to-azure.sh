#!/bin/bash
# Non-interactive Azure Container App deployment script for EdutainmentForge
# Uses existing infrastructure and Key Vault secrets

set -e

# Configuration (using existing resources)
RESOURCE_GROUP="edutainmentforge-rg"
SUBSCRIPTION_ID="e440a65b-7418-4865-9821-88e411ffdd5b"
CONTAINER_REGISTRY_NAME="edutainmentforge"
CONTAINER_APP_NAME="edutainmentforge-app"
CONTAINER_IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting non-interactive Azure Container deployment for EdutainmentForge${NC}"

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged into Azure
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged into Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Set subscription
echo -e "${BLUE}📋 Setting Azure subscription...${NC}"
az account set --subscription $SUBSCRIPTION_ID

# Get current subscription info
CURRENT_SUB=$(az account show --query id -o tsv)
echo -e "${GREEN}✅ Using subscription: $CURRENT_SUB${NC}"

# Verify resource group exists
echo -e "${BLUE}🏗️  Verifying resource group exists...${NC}"
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}❌ Resource group '$RESOURCE_GROUP' not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Resource group verified${NC}"

# Verify container registry exists
echo -e "${BLUE}📦 Verifying container registry exists...${NC}"
if ! az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}❌ Container registry '$CONTAINER_REGISTRY_NAME' not found${NC}"
    exit 1
fi

# Get container registry login server
CONTAINER_REGISTRY_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
echo -e "${GREEN}✅ Container registry verified: $CONTAINER_REGISTRY_LOGIN_SERVER${NC}"

# Verify container app exists
echo -e "${BLUE}📱 Verifying container app exists...${NC}"
if ! az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}❌ Container app '$CONTAINER_APP_NAME' not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Container app verified${NC}"

# Build the Docker image
echo -e "${BLUE}🐳 Building Docker image...${NC}"
docker build -t edutainmentforge:$CONTAINER_IMAGE_TAG .

# Tag for ACR
FULL_IMAGE_NAME="$CONTAINER_REGISTRY_LOGIN_SERVER/edutainmentforge:$CONTAINER_IMAGE_TAG"
echo -e "${BLUE}🏷️  Tagging image: $FULL_IMAGE_NAME${NC}"
docker tag edutainmentforge:$CONTAINER_IMAGE_TAG $FULL_IMAGE_NAME

# Login to ACR and push
echo -e "${BLUE}🔐 Logging into Azure Container Registry...${NC}"
az acr login --name $CONTAINER_REGISTRY_NAME

echo -e "${BLUE}📤 Pushing image to ACR...${NC}"
docker push $FULL_IMAGE_NAME

# Update container app with new image
echo -e "${BLUE}🔄 Updating container app with new image...${NC}"
az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --image $FULL_IMAGE_NAME \
    --output table

# Get the app URL
CONTAINER_APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo -e "   Resource Group: $RESOURCE_GROUP"
echo -e "   Container Registry: $CONTAINER_REGISTRY_NAME"
echo -e "   Container App: $CONTAINER_APP_NAME"
echo -e "   Image: $FULL_IMAGE_NAME"
echo -e "   App URL: https://$CONTAINER_APP_URL"
echo ""
echo -e "${GREEN}🔑 All secrets are automatically loaded from Azure Key Vault${NC}"
echo -e "${GREEN}🎉 Your authenticated EdutainmentForge app is ready!${NC}"
echo ""
echo -e "${BLUE}💡 To test authentication, visit: https://$CONTAINER_APP_URL${NC}"
