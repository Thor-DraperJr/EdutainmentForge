#!/bin/bash
# Container build script for EdutainmentForge

set -e

echo "🐳 Building EdutainmentForge Container"
echo "===================================="

REGISTRY="edutainmentforge.azurecr.io"
IMAGE_NAME="edutainmentforge"
TAG="latest"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "📋 Build Configuration:"
echo "  Registry: ${REGISTRY}"
echo "  Image: ${IMAGE_NAME}"
echo "  Tag: ${TAG}"
echo "  Full Image: ${FULL_IMAGE}"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🔨 Building with local Docker..."
    
    # Build the image
    docker build -t ${FULL_IMAGE} .
    
    # Login to Azure Container Registry
    echo "🔐 Logging into Azure Container Registry..."
    az acr login --name edutainmentforge
    
    # Push the image
    echo "📤 Pushing image to registry..."
    docker push ${FULL_IMAGE}
    
    echo "✅ Local Docker build completed!"
else
    echo "🌥️  Docker not available locally, using Azure Container Registry build..."
    
    # Use ACR build (cloud build)
    az acr build \
        --registry edutainmentforge \
        --image ${IMAGE_NAME}:${TAG} \
        --file Dockerfile \
        .
    
    echo "✅ Cloud build completed!"
fi

echo "🎯 Image ready: ${FULL_IMAGE}"
