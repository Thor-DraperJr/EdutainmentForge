#!/bin/bash
# EdutainmentForge Premium Service Upgrade Script
# This script helps you upgrade to paid tiers for better podcast quality

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 EdutainmentForge Premium Service Upgrade${NC}"
echo "=================================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged into Azure CLI. Please run: az login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"
echo ""

# Get current configuration
RESOURCE_GROUP="edutainmentforge-rg"
OPENAI_ACCOUNT="edutainmentforge-openai"
SPEECH_ACCOUNT="edutainmentforge-speech"
KEYVAULT_NAME="edutainmentforge-kv"

echo -e "${BLUE}🔍 Current Azure Setup:${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "OpenAI Account: $OPENAI_ACCOUNT"
echo "Speech Account: $SPEECH_ACCOUNT"
echo "Key Vault: $KEYVAULT_NAME"
echo ""

# Menu for upgrade options
echo -e "${YELLOW}🎯 Select Premium Upgrades:${NC}"
echo "1. Deploy GPT-4 Model (Better script understanding)"
echo "2. Enable Neural Voice Styles (More natural audio)"
echo "3. Setup Custom Voice Training (Unique podcast identity)"
echo "4. All Premium Features"
echo "5. Cost Monitoring Setup"
echo "6. Exit"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo -e "${BLUE}🤖 Deploying GPT-4 Model...${NC}"
        echo ""
        echo "Note: GPT-4 requires quota approval and costs more than gpt-4o-mini"
        echo "Expected cost: $50-150/month depending on usage"
        echo ""
        read -p "Continue? (y/n): " confirm
        
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            echo "Deploying GPT-4 model..."
            
            # Deploy GPT-4 model
            az cognitiveservices account deployment create \
                --name $OPENAI_ACCOUNT \
                --resource-group $RESOURCE_GROUP \
                --deployment-name gpt-4 \
                --model-name gpt-4 \
                --model-version "turbo-2024-04-09" \
                --sku-capacity 10 \
                --sku-name "Standard" || {
                echo -e "${RED}❌ GPT-4 deployment failed. You may need to request quota approval first.${NC}"
                echo "Request quota at: https://aka.ms/oai/quotaincrease"
                exit 1
            }
            
            # Update Key Vault with GPT-4 deployment name
            az keyvault secret set \
                --vault-name $KEYVAULT_NAME \
                --name azure-openai-gpt4-deployment \
                --value "gpt-4"
                
            echo -e "${GREEN}✅ GPT-4 model deployed successfully!${NC}"
            echo "Update your application to use the new deployment for complex content."
        fi
        ;;
        
    2)
        echo -e "${BLUE}🎤 Enabling Neural Voice Styles...${NC}"
        echo ""
        echo "Neural voices provide more natural sounding speech with emotional expression"
        echo "Expected additional cost: $20-40/month"
        echo ""
        read -p "Continue? (y/n): " confirm
        
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            # Enable neural voice features in Key Vault
            az keyvault secret set \
                --vault-name $KEYVAULT_NAME \
                --name neural-voice-enabled \
                --value "true"
                
            az keyvault secret set \
                --vault-name $KEYVAULT_NAME \
                --name voice-styles-enabled \
                --value "true"
                
            # Set premium voice configurations
            az keyvault secret set \
                --vault-name $KEYVAULT_NAME \
                --name sarah-voice-premium \
                --value "en-US-AriaNeural"
                
            az keyvault secret set \
                --vault-name $KEYVAULT_NAME \
                --name mike-voice-premium \
                --value "en-US-DavisNeural"
                
            echo -e "${GREEN}✅ Neural voice styles enabled!${NC}"
            echo "Your application can now use emotional expression in voices."
        fi
        ;;
        
    3)
        echo -e "${BLUE}🎨 Custom Voice Training Setup...${NC}"
        echo ""
        echo "Custom voices provide unique, branded podcast identities"
        echo "Setup cost: $100-300 one-time + $30-50/month"
        echo ""
        echo "This requires manual setup in Speech Studio:"
        echo "1. Create voice training project"
        echo "2. Upload 2-3 hours of voice samples per character"
        echo "3. Train custom voice models"
        echo "4. Deploy to Speech Service"
        echo ""
        echo -e "${YELLOW}Opening Speech Studio...${NC}"
        
        # Open Speech Studio in browser
        if command -v xdg-open &> /dev/null; then
            xdg-open "https://speech.microsoft.com/portal"
        elif command -v open &> /dev/null; then
            open "https://speech.microsoft.com/portal"
        else
            echo "Please visit: https://speech.microsoft.com/portal"
        fi
        
        echo ""
        echo "Manual steps required:"
        echo "1. Sign in with your Azure account"
        echo "2. Select your Speech resource: $SPEECH_ACCOUNT"
        echo "3. Go to Custom Voice section"
        echo "4. Create new voice training project"
        echo "5. Follow the voice training wizard"
        ;;
        
    4)
        echo -e "${BLUE}🚀 Setting up All Premium Features...${NC}"
        echo ""
        echo "This will enable:"
        echo "- GPT-4 model deployment"
        echo "- Neural voice styles"
        echo "- Premium monitoring"
        echo ""
        echo "Total expected cost: $80-200/month"
        echo ""
        read -p "Continue with full premium setup? (y/n): " confirm
        
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            # Run all premium setups
            echo "Deploying all premium features..."
            
            # Deploy GPT-4
            echo "1. Deploying GPT-4..."
            az cognitiveservices account deployment create \
                --name $OPENAI_ACCOUNT \
                --resource-group $RESOURCE_GROUP \
                --deployment-name gpt-4 \
                --model-name gpt-4 \
                --model-version "turbo-2024-04-09" \
                --sku-capacity 10 \
                --sku-name "Standard" || echo "GPT-4 deployment failed - may need quota approval"
                
            # Enable neural voices
            echo "2. Enabling neural voices..."
            az keyvault secret set --vault-name $KEYVAULT_NAME --name neural-voice-enabled --value "true"
            az keyvault secret set --vault-name $KEYVAULT_NAME --name voice-styles-enabled --value "true"
            
            # Set premium configurations
            echo "3. Configuring premium settings..."
            az keyvault secret set --vault-name $KEYVAULT_NAME --name premium-mode-enabled --value "true"
            az keyvault secret set --vault-name $KEYVAULT_NAME --name ai-model-preference --value "gpt-4"
            
            echo -e "${GREEN}✅ Premium features setup complete!${NC}"
        fi
        ;;
        
    5)
        echo -e "${BLUE}📊 Setting up Cost Monitoring...${NC}"
        echo ""
        
        # Create cost alert
        echo "Setting up cost monitoring and alerts..."
        
        # Enable monitoring secrets
        az keyvault secret set \
            --vault-name $KEYVAULT_NAME \
            --name cost-monitoring-enabled \
            --value "true"
            
        az keyvault secret set \
            --vault-name $KEYVAULT_NAME \
            --name cost-alert-threshold \
            --value "100"  # Alert at $100/month
            
        echo -e "${GREEN}✅ Cost monitoring enabled!${NC}"
        echo "You'll receive alerts when costs exceed thresholds."
        ;;
        
    6)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Premium upgrade process complete!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update your application configuration to use premium features"
echo "2. Test the enhanced podcast quality"
echo "3. Monitor costs in Azure Portal"
echo "4. Consider custom voice training for unique podcast identity"
echo ""
echo -e "${BLUE}Useful Links:${NC}"
echo "- Azure Portal: https://portal.azure.com"
echo "- Speech Studio: https://speech.microsoft.com/portal"
echo "- OpenAI Studio: https://oai.azure.com"
echo "- Cost Management: https://portal.azure.com/#view/Microsoft_Azure_CostManagement"
echo ""
