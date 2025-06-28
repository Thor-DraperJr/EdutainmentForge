# Azure Container Apps Deployment Configuration

## Prerequisites
- Azure CLI installed and logged in
- Resource group created
- Azure Container Apps Environment created
- Azure Speech Service resource created

## Environment Variables Required
- AZURE_SPEECH_KEY: Your Azure Speech Service key
- AZURE_SPEECH_REGION: Your Azure Speech Service region

## Deployment Steps

### 1. Build and Push Container Image
```bash
# Build the container image
docker build -t edutainmentforge:latest .

# Tag for Azure Container Registry
docker tag edutainmentforge:latest <your-acr-name>.azurecr.io/edutainmentforge:latest

# Push to ACR
az acr login --name <your-acr-name>
docker push <your-acr-name>.azurecr.io/edutainmentforge:latest
```

### 2. Deploy to Azure Container Apps
```bash
# Create the container app
az containerapp create \
  --name edutainmentforge \
  --resource-group <your-resource-group> \
  --environment <your-container-apps-environment> \
  --image <your-acr-name>.azurecr.io/edutainmentforge:latest \
  --target-port 5000 \
  --ingress external \
  --env-vars \
    AZURE_SPEECH_KEY=secretref:azure-speech-key \
    AZURE_SPEECH_REGION=<your-region> \
    FLASK_ENV=production \
    SARAH_VOICE=en-US-AriaNeural \
    MIKE_VOICE=en-US-DavisNeural \
  --secrets \
    azure-speech-key=<your-azure-speech-key> \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 10
```

### 3. Configure Storage (Optional)
If you need persistent storage for generated podcasts:
```bash
# Create Azure Storage Account
az storage account create \
  --name <your-storage-account> \
  --resource-group <your-resource-group> \
  --location <your-location> \
  --sku Standard_LRS

# Mount storage to container app
az containerapp update \
  --name edutainmentforge \
  --resource-group <your-resource-group> \
  --set-env-vars AZURE_STORAGE_ACCOUNT=<your-storage-account>
```

### 4. Monitor and Scale
```bash
# View logs
az containerapp logs show \
  --name edutainmentforge \
  --resource-group <your-resource-group>

# Update scaling rules
az containerapp update \
  --name edutainmentforge \
  --resource-group <your-resource-group> \
  --min-replicas 0 \
  --max-replicas 20
```

## Security Considerations
- Use Managed Identity for Azure service authentication
- Store secrets in Azure Key Vault
- Enable HTTPS ingress
- Configure network policies if needed
- Use least privilege RBAC roles
