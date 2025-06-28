@description('Location for all resources')
param location string = 'eastus2'

@description('Environment name for the Container App')
param environmentName string = 'edutainmentforge-env'

@description('Container App name')
param containerAppName string = 'edutainmentforge-app'

@description('Container Registry name')
param acrName string = 'edutainmentforge'

@description('Azure Speech Service key')
@secure()
param azureSpeechKey string

@description('Key Vault name')
param keyVaultName string = 'edutainmentforge-kv'

// Use existing resource group
resource existingResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = {
  name: 'edutainmentforge-rg'
  scope: subscription()
}

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

// Key Vault for secrets
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false
  }
}

// Store Azure Speech key in Key Vault
resource speechKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'azure-speech-key'
  properties: {
    value: azureSpeechKey
  }
}

// Log Analytics Workspace for Container App monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${environmentName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
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

// Container App with managed identity
resource containerApp 'Microsoft.App/containerapps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      secrets: [
        {
          name: 'azure-speech-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-speech-key'
          identity: 'system'
        }
      ]
      ingress: {
        external: true
        targetPort: 5000
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'edutainmentforge'
          image: '${acr.properties.loginServer}/edutainmentforge:latest'
          resources: {
            cpu: json('1')
            memory: '2Gi'
          }
          env: [
            {
              name: 'FLASK_ENV'
              value: 'production'
            }
            {
              name: 'AZURE_SPEECH_KEY'
              secretRef: 'azure-speech-key'
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: location
            }
            {
              name: 'SARAH_VOICE'
              value: 'en-US-AriaNeural'
            }
            {
              name: 'MIKE_VOICE'
              value: 'en-US-DavisNeural'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Grant Key Vault access to Container App managed identity
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, containerApp.id, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output acrLoginServer string = acr.properties.loginServer
output keyVaultName string = keyVault.name
output resourceGroupName string = 'edutainmentforge-rg'
