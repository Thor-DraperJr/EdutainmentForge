#!/bin/bash
# Secure deployment script for EdutainmentForge to Azure Container Apps

set -e

echo "🚀 EdutainmentForge Secure Deployment to Azure Container Apps"
echo "============================================================"

# Configuration
REGISTRY_NAME="edutainmentforge"
RESOURCE_GROUP="edutainmentforge-rg"
CONTAINER_APP_NAME="edutainmentforge-app"
CONTAINER_ENV_NAME="edutainmentforge-env"
IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"

echo "📦 Building container image..."
echo "Registry: ${REGISTRY_NAME}.azurecr.io"
echo "Image tag: ${IMAGE_TAG}"

# Build the container using Azure Container Registry (cloud build)
echo "🔨 Building container in Azure..."
az acr build \
  --registry $REGISTRY_NAME \
  --image edutainmentforge:latest \
  --image edutainmentforge:$IMAGE_TAG \
  --file Dockerfile \
  .

echo "✅ Container built successfully!"

# Enable system-assigned managed identity for Container App Environment
echo "🔐 Configuring managed identity..."
az containerapp env update \
  --name $CONTAINER_ENV_NAME \
  --resource-group $RESOURCE_GROUP

# Grant Key Vault access to the managed identity
echo "🔑 Granting Key Vault permissions..."
PRINCIPAL_ID=$(az containerapp env show \
  --name $CONTAINER_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId \
  --output tsv)

if [ -n "$PRINCIPAL_ID" ]; then
  az keyvault set-policy \
    --name edutainmentforge-kv \
    --object-id $PRINCIPAL_ID \
    --secret-permissions get list
  echo "✅ Key Vault permissions granted!"
else
  echo "⚠️  Warning: Could not retrieve managed identity. Manual setup may be required."
fi

# Deploy/update container app with secure configuration
echo "🚀 Deploying container app..."
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --yaml azure-container-app.yaml

echo "✅ Deployment completed!"
echo "🌐 Application URL: https://${CONTAINER_APP_NAME}.happyflower-12345678.eastus2.azurecontainerapps.io"
echo "📊 Monitor at: https://portal.azure.com/#@/resource/subscriptions/4bc4983d-aa44-48da-a77c-4ec0e1fd1ae9/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/${CONTAINER_APP_NAME}"
