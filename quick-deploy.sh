#!/bin/bash
# Quick ACR build and deployment

echo "Building container with ACR..."

# Create a tar file of the source code (excluding unnecessary files)
tar -czf source.tar.gz \
  --exclude='.git' \
  --exclude='cache' \
  --exclude='output' \
  --exclude='temp' \
  --exclude='logs' \
  --exclude='tests' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  .

# Upload and build
az acr build \
  --registry edutainmentforge \
  --image edutainmentforge:latest \
  --file Dockerfile \
  source.tar.gz

# Clean up
rm source.tar.gz

echo "Build completed! Updating container app..."

# Update the container app to trigger a new revision
az containerapp update \
  --name edutainmentforge-app \
  --resource-group edutainmentforge-rg \
  --image edutainmentforge.azurecr.io/edutainmentforge:latest

echo "Deployment complete!"
