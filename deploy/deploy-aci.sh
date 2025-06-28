#!/bin/bash

# Simple Azure Container Instances deployment script
# Alternative to Container Apps for simpler deployment

set -e

RESOURCE_GROUP="edutainmentforge-rg"
LOCATION="eastus2"
CONTAINER_NAME="edutainmentforge-aci"
IMAGE_NAME="edutainmentforge:latest"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Deploying to Azure Container Instances...${NC}"

# Prompt for Azure Speech Service key
echo -e "${YELLOW}🔑 Please enter your Azure Speech Service key:${NC}"
read -s AZURE_SPEECH_KEY

if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo -e "${RED}❌ Azure Speech Service key is required!${NC}"
    exit 1
fi

# Build image locally
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
docker build -t "$IMAGE_NAME" .

# Create a temporary ACR for the image (if not using existing one)
ACR_NAME="edutainmentforge$(date +%s)"
echo -e "${YELLOW}📦 Creating temporary Azure Container Registry...${NC}"
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --location "$LOCATION"

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query passwords[0].value --output tsv)

# Login and push
echo -e "${YELLOW}📤 Pushing to ACR...${NC}"
az acr login --name "$ACR_NAME"
docker tag "$IMAGE_NAME" "$ACR_LOGIN_SERVER/edutainmentforge:latest"
docker push "$ACR_LOGIN_SERVER/edutainmentforge:latest"

# Deploy to ACI
echo -e "${YELLOW}☁️  Deploying to Azure Container Instances...${NC}"
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --image "$ACR_LOGIN_SERVER/edutainmentforge:latest" \
    --registry-login-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --dns-name-label "$CONTAINER_NAME" \
    --ports 5000 \
    --cpu 1 \
    --memory 2 \
    --environment-variables \
        FLASK_ENV=production \
        AZURE_SPEECH_REGION="$LOCATION" \
        SARAH_VOICE=en-US-AriaNeural \
        MIKE_VOICE=en-US-DavisNeural \
    --secure-environment-variables \
        AZURE_SPEECH_KEY="$AZURE_SPEECH_KEY" \
    --location "$LOCATION"

# Get the FQDN
FQDN=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query ipAddress.fqdn --output tsv)

echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo -e "${GREEN}🌐 Application URL: http://$FQDN:5000${NC}"
echo -e "${YELLOW}📝 Note: This uses HTTP. For production, consider using Container Apps with custom domain and SSL.${NC}"
