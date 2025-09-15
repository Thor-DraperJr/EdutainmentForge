#!/bin/bash

# Azure AD B2C Setup Script for EdutainmentForge
# This script helps set up Azure AD B2C authentication

set -e

echo "🔐 EdutainmentForge - Azure AD B2C Setup"
echo "========================================"
echo

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo "✅ Azure CLI found"

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "🔑 Please log in to Azure CLI:"
    az login
fi

echo "✅ Azure CLI authenticated"
echo

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "📋 Current subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
echo

# Check if resource group exists
RESOURCE_GROUP="edutainmentforge-rg"
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Resource group '$RESOURCE_GROUP' not found."
    echo "   Please ensure your EdutainmentForge infrastructure is deployed first."
    exit 1
fi

echo "✅ Resource group '$RESOURCE_GROUP' found"
echo

# Create Azure AD B2C tenant (manual step - requires portal)
echo "🚧 Manual Step Required: Create Azure AD B2C Tenant"
echo "=================================================="
echo "1. Go to the Azure Portal: https://portal.azure.com"
echo "2. Search for 'Azure AD B2C' and create a new tenant"
echo "3. Choose 'Create a new Azure AD B2C Tenant'"
echo "4. Organization name: EdutainmentForge"
echo "5. Initial domain name: edutainmentforge (or similar if taken)"
echo "6. Location: United States"
echo
read -p "Press Enter when you have created the B2C tenant..."
echo

# Get B2C tenant information
echo "🔧 B2C Tenant Configuration"
echo "============================="
read -p "Enter your B2C tenant name (without .onmicrosoft.com): " B2C_TENANT
read -p "Enter your B2C tenant ID (from tenant overview): " B2C_TENANT_ID

# Create app registration (manual step - requires portal)
echo
echo "🚧 Manual Step Required: Create App Registration"
echo "==============================================="
echo "1. In your B2C tenant, go to 'App registrations'"
echo "2. Click 'New registration'"
echo "3. Name: EdutainmentForge Web App"
echo "4. Supported account types: Accounts in any identity provider or organizational directory"
echo "5. Redirect URI: Web - http://localhost:5000/auth/callback"
echo "6. After creation, add production redirect URI in Authentication:"
echo "   - https://your-production-domain.com/auth/callback"
echo
read -p "Press Enter when you have created the app registration..."
echo

# Get app registration information
read -p "Enter your App Registration Client ID: " CLIENT_ID
echo

echo "🔧 Creating Client Secret"
echo "========================="
echo "1. In your app registration, go to 'Certificates & secrets'"
echo "2. Click 'New client secret'"
echo "3. Description: EdutainmentForge Production Secret"
echo "4. Expires: 24 months"
echo "5. Copy the secret VALUE (not the ID)"
echo
read -p "Enter your Client Secret VALUE: " CLIENT_SECRET
echo

# Create user flow (manual step)
echo "🚧 Manual Step Required: Create User Flow"
echo "========================================="
echo "1. In your B2C tenant, go to 'User flows'"
echo "2. Click 'New user flow'"
echo "3. Select 'Sign up and sign in'"
echo "4. Version: Recommended"
echo "5. Name: SignUpSignIn"
echo "6. Identity providers: Email signup"
echo "7. User attributes and claims:"
echo "   - Collect: Email Address, Display Name, Given Name, Surname"
echo "   - Return: Email Addresses, Display Name, Given Name, Surname, User's Object ID"
echo "8. Create the user flow"
echo
read -p "Press Enter when you have created the user flow..."
echo

# Check for Key Vault
KEY_VAULT_NAME="edutainmentforge-kv"
if ! az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Key Vault '$KEY_VAULT_NAME' not found in resource group '$RESOURCE_GROUP'"
    echo "   Please ensure your EdutainmentForge infrastructure is deployed first."
    exit 1
fi

echo "✅ Key Vault '$KEY_VAULT_NAME' found"
echo

# Store secrets in Key Vault
echo "🔐 Storing secrets in Azure Key Vault"
echo "====================================="

# Set the secrets
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-tenant-id" --value "$B2C_TENANT" --description "Azure AD B2C tenant name"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-client-id" --value "$CLIENT_ID" --description "Azure AD B2C application client ID"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-client-secret" --value "$CLIENT_SECRET" --description "Azure AD B2C application client secret"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "azure-ad-b2c-policy-name" --value "B2C_1_SignUpSignIn" --description "Azure AD B2C user flow policy name"

# Generate Flask secret key
FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "flask-secret-key" --value "$FLASK_SECRET" --description "Flask session secret key"

echo "✅ All secrets stored in Key Vault"
echo

# Create local .env file for development
echo "📝 Creating local .env file"
echo "============================"

cat > .env << EOF
# Azure Speech Service
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus2

# Azure OpenAI Service
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://edutainmentforge-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Voice Configuration
SARAH_VOICE=en-US-EmmaNeural
MIKE_VOICE=en-US-DavisNeural

# Azure AD B2C Configuration
AZURE_AD_B2C_TENANT_ID=$B2C_TENANT
AZURE_AD_B2C_CLIENT_ID=$CLIENT_ID
AZURE_AD_B2C_CLIENT_SECRET=$CLIENT_SECRET
AZURE_AD_B2C_POLICY_NAME=B2C_1_SignUpSignIn

# Flask Configuration
FLASK_SECRET_KEY=$FLASK_SECRET
EOF

echo "✅ Local .env file created"
echo

# Final instructions
echo "🎉 Azure AD B2C Setup Complete!"
echo "==============================="
echo
echo "Next steps:"
echo "1. Update your .env file with your Azure Speech and OpenAI keys"
echo "2. Test authentication locally: python app.py"
echo "3. Push changes to 'main' branch (CI will build & deploy container)"
echo "   (Manual redeploy rarely needed; see docs/AUTHENTICATION.md for fallback CLI)"
echo
echo "🔗 URLs to remember:"
echo "- B2C Tenant Portal: https://portal.azure.com/#view/Microsoft_AAD_B2CAdmin"
echo "- User Flow: https://$B2C_TENANT.b2clogin.com/$B2C_TENANT.onmicrosoft.com/B2C_1_SignUpSignIn/oauth2/v2.0/authorize"
echo "- Local dev: http://localhost:5000/auth/login"
echo
echo "✅ Setup complete! You can now use Azure AD B2C authentication."
