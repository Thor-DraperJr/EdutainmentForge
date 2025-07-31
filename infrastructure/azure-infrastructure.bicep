@description('The location for all resources')
param location string = resourceGroup().location

@description('The prefix for all resource names')
param resourcePrefix string = 'edutainmentforge'

@description('The container image to deploy')
param containerImage string = 'edutainmentforge.azurecr.io/edutainmentforge:latest'

@description('The Azure Speech Service region')
param azureSpeechRegion string = location

@description('The Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-02-15-preview'

@description('The Azure OpenAI deployment name')
param azureOpenAiDeploymentName string = 'gpt-4o-mini'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${resourcePrefix}stor${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${resourcePrefix}registry'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Key Vault (RBAC-enabled for modern security)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${resourcePrefix}-kv'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true  // Use RBAC instead of access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false
    networkAcls: {
      defaultAction: 'Deny'  // Network-restricted for enhanced security
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${resourcePrefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${resourcePrefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${resourcePrefix}-app'
  location: location
  identity: {
    type: 'SystemAssigned'  // Use system-assigned managed identity (matches current setup)
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 5000
        transport: 'http'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'azure-speech-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-speech-key'
          identity: 'system'  // Use system-assigned identity for Key Vault access
        }
        {
          name: 'azure-openai-api-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-api-key'
          identity: 'system'
        }
        {
          name: 'azure-openai-endpoint'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-endpoint'
          identity: 'system'
        }
        {
          name: 'sarah-voice'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/sarah-voice'
          identity: 'system'
        }
        {
          name: 'mike-voice'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/mike-voice'
          identity: 'system'
        }
        {
          name: 'flask-secret-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/flask-secret-key'
          identity: 'system'
        }
        {
          name: 'azure-ad-b2c-tenant-id'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-ad-b2c-tenant-id'
          identity: 'system'
        }
        {
          name: 'azure-ad-b2c-client-id'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-ad-b2c-client-id'
          identity: 'system'
        }
        {
          name: 'azure-ad-b2c-client-secret'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-ad-b2c-client-secret'
          identity: 'system'
        }
        {
          name: 'azure-ad-b2c-policy-name'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-ad-b2c-policy-name'
          identity: 'system'
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
      ]
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: 'system'  // Use system-assigned identity for ACR access
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'edutainmentforge'
          image: containerImage
          env: [
            {
              name: 'AZURE_SPEECH_KEY'
              secretRef: 'azure-speech-key'
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: azureSpeechRegion
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              secretRef: 'azure-openai-endpoint'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-api-key'
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAiApiVersion
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: azureOpenAiDeploymentName
            }
            {
              name: 'FLASK_ENV'
              value: 'production'
            }
            {
              name: 'SARAH_VOICE'
              secretRef: 'sarah-voice'
            }
            {
              name: 'MIKE_VOICE'
              secretRef: 'mike-voice'
            }
            {
              name: 'FLASK_SECRET_KEY'
              secretRef: 'flask-secret-key'
            }
            {
              name: 'AZURE_AD_B2C_TENANT_ID'
              secretRef: 'azure-ad-b2c-tenant-id'
            }
            {
              name: 'AZURE_AD_B2C_CLIENT_ID'
              secretRef: 'azure-ad-b2c-client-id'
            }
            {
              name: 'AZURE_AD_B2C_CLIENT_SECRET'
              secretRef: 'azure-ad-b2c-client-secret'
            }
            {
              name: 'AZURE_AD_B2C_POLICY_NAME'
              secretRef: 'azure-ad-b2c-policy-name'
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
      }
    }
  }
}

// Role Assignment for ACR Pull
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, containerApp.id, 'AcrPull')
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role Assignment for Key Vault Secrets User (read-only access to secrets)
resource keyVaultSecretsUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerApp.id, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output containerAppPrincipalId string = containerApp.identity.principalId
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
