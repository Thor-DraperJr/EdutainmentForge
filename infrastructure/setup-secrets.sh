#!/bin/bash

# Azure Infrastructure Post-Deployment Secret Setup
# This script sets up all the required secrets in Key Vault after infrastructure deployment
# Requires RBAC permissions: Key Vault Secrets Officer or Key Vault Administrator

set -e

# Configuration
RESOURCE_GROUP="edutainmentforge-rg"
KEY_VAULT_NAME="edutainmentforge-kv"

echo "🔧 Setting up EdutainmentForge Key Vault secrets..."
echo "📋 Note: This script requires 'Key Vault Secrets Officer' or 'Key Vault Administrator' role"

# Check if we're logged in to Azure
if ! az account show &>/dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Check if Key Vault exists and uses RBAC
if ! az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "❌ Key Vault $KEY_VAULT_NAME not found in resource group $RESOURCE_GROUP"
    echo "Please deploy the infrastructure first using:"
    echo "  az deployment group create --resource-group $RESOURCE_GROUP --template-file azure-infrastructure-clean.bicep"
    exit 1
fi

# Verify RBAC is enabled
RBAC_ENABLED=$(az keyvault show --name $KEY_VAULT_NAME --query "properties.enableRbacAuthorization" -o tsv)
if [ "$RBAC_ENABLED" != "true" ]; then
    echo "❌ Key Vault $KEY_VAULT_NAME does not have RBAC enabled"
    echo "This deployment requires RBAC authorization for modern security"
    exit 1
fi

echo "✅ Key Vault found: $KEY_VAULT_NAME (RBAC enabled)"

# Check user permissions
CURRENT_USER=$(az account show --query user.name -o tsv)
echo "🔍 Checking RBAC permissions for user: $CURRENT_USER"

# Try to list secrets as a permission test
if ! az keyvault secret list --vault-name $KEY_VAULT_NAME --query "[0].name" -o tsv &>/dev/null; then
    echo "❌ Insufficient permissions to manage secrets in Key Vault $KEY_VAULT_NAME"
    echo ""
    echo "Required roles (assign one):"
    echo "  - Key Vault Secrets Officer (recommended)"
    echo "  - Key Vault Administrator" 
    echo "  - Owner or Contributor on the resource group"
    echo ""
    echo "To assign the recommended role:"
    echo "  az role assignment create --role 'Key Vault Secrets Officer' --assignee $CURRENT_USER --scope /subscriptions/\$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"
    exit 1
fi

echo "✅ Permissions verified: Can manage secrets"

# Function to set secret if it doesn't exist or if user wants to update
set_secret_if_needed() {
    local secret_name=$1
    local prompt_message=$2
    local is_secure=${3:-true}
    
    # Check if secret exists
    if az keyvault secret show --vault-name $KEY_VAULT_NAME --name $secret_name &>/dev/null; then
        echo "⚠️  Secret '$secret_name' already exists."
        read -p "Do you want to update it? (y/N): " update_choice
        if [[ ! $update_choice =~ ^[Yy]$ ]]; then
            echo "⏭️  Skipping $secret_name"
            return
        fi
    fi
    
    if [ "$is_secure" = true ]; then
        echo ""
        read -s -p "$prompt_message: " secret_value
        echo ""
    else
        echo ""
        read -p "$prompt_message: " secret_value
    fi
    
    if [ -n "$secret_value" ]; then
        az keyvault secret set --vault-name $KEY_VAULT_NAME --name $secret_name --value "$secret_value" --output none
        echo "✅ Set secret: $secret_name"
    else
        echo "⚠️  Empty value provided, skipping $secret_name"
    fi
}

echo ""
echo "📋 Setting up Azure service secrets..."
echo "You'll need to provide the following information:"
echo "  1. Azure Speech Service key and region"
echo "  2. Azure OpenAI API key and endpoint"
echo "  3. Azure AD B2C configuration"
echo "  4. Voice configuration"
echo ""

# Azure Speech Service
set_secret_if_needed "azure-speech-key" "Enter Azure Speech Service Key"

# Azure OpenAI
set_secret_if_needed "azure-openai-api-key" "Enter Azure OpenAI API Key"
set_secret_if_needed "azure-openai-endpoint" "Enter Azure OpenAI Endpoint (e.g., https://your-openai.openai.azure.com/)" false

# Voice Configuration
echo ""
echo "🎙️ Setting up voice configuration..."
echo "Current recommended voices:"
echo "  Sarah: en-US-EmmaNeural (premium female voice)"
echo "  Mike: en-US-DavisNeural (premium male voice)"
echo ""

# Check if voice secrets exist, if not set defaults
if ! az keyvault secret show --vault-name $KEY_VAULT_NAME --name "sarah-voice" &>/dev/null; then
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "sarah-voice" --value "en-US-EmmaNeural" --output none
    echo "✅ Set default Sarah voice: en-US-EmmaNeural"
else
    set_secret_if_needed "sarah-voice" "Enter Sarah's voice (press Enter for current value)" false
fi

if ! az keyvault secret show --vault-name $KEY_VAULT_NAME --name "mike-voice" &>/dev/null; then
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "mike-voice" --value "en-US-DavisNeural" --output none
    echo "✅ Set default Mike voice: en-US-DavisNeural"
else
    set_secret_if_needed "mike-voice" "Enter Mike's voice (press Enter for current value)" false
fi

# Flask Secret Key
if ! az keyvault secret show --vault-name $KEY_VAULT_NAME --name "flask-secret-key" &>/dev/null; then
    # Generate a secure random key
    flask_secret=$(openssl rand -base64 32)
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "flask-secret-key" --value "$flask_secret" --output none
    echo "✅ Generated Flask secret key"
else
    echo "⏭️  Flask secret key already exists"
fi

# Azure AD B2C Configuration
echo ""
echo "🔐 Setting up Azure AD B2C authentication..."
echo "You'll need to create an Azure AD B2C tenant and app registration first."
echo "See: https://docs.microsoft.com/en-us/azure/active-directory-b2c/tutorial-create-tenant"
echo ""

set_secret_if_needed "azure-ad-b2c-tenant-id" "Enter Azure AD B2C Tenant ID (e.g., yourtenant.onmicrosoft.com)" false
set_secret_if_needed "azure-ad-b2c-client-id" "Enter Azure AD B2C Application (client) ID" false
set_secret_if_needed "azure-ad-b2c-client-secret" "Enter Azure AD B2C Client Secret"

# Azure AD B2C Policy Name
if ! az keyvault secret show --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-policy-name" &>/dev/null; then
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-policy-name" --value "B2C_1_signupsignin" --output none
    echo "✅ Set default B2C policy name: B2C_1_signupsignin"
else
    set_secret_if_needed "azure-ad-b2c-policy-name" "Enter Azure AD B2C Policy Name (press Enter for B2C_1_signupsignin)" false
fi

echo ""
echo "🎉 Secret setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Verify your Azure services are deployed and configured"
echo "  2. Build and push your container image:"
echo "     ./scripts/build-container.sh"
echo "  3. Deploy the container app:"
echo "     az deployment group create --resource-group $RESOURCE_GROUP --template-file azure-infrastructure-clean.bicep"
echo ""
echo "🔍 To view all secrets:"
echo "  az keyvault secret list --vault-name $KEY_VAULT_NAME --query '[].name' -o tsv"
echo ""
echo "🔐 To update a secret later:"
echo "  az keyvault secret set --vault-name $KEY_VAULT_NAME --name SECRET_NAME --value 'new-value'"
