@description('The location for all resources')
param location string = resourceGroup().location

@description('The name prefix for all resources')
param namePrefix string = 'edutainment'

@description('The Azure Speech Service region')
param azureSpeechRegion string = location

@description('The Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-02-15-preview'

@description('The Azure OpenAI deployment name')
param azureOpenAiDeploymentName string = 'gpt-4o-mini'

@description('Container image reference')
param containerImage string

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-10-01' = {
  name: '${namePrefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// User Assigned Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-identity'
  location: location
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: '${namePrefix}acr${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

// Role assignment for managed identity to pull from ACR
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(containerRegistry.id, managedIdentity.id, 'AcrPull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage Account for generated podcasts
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${namePrefix}storage${uniqueString(resourceGroup().id)}'
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

// Blob container for podcasts
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/podcasts'
  properties: {
    publicAccess: 'None'
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2022-10-01' = {
  name: '${namePrefix}-app'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
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
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'azure-openai-api-key'
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'azure-openai-endpoint'
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'sarah-voice'
          value: 'en-US-EmmaNeural'
        }
        {
          name: 'mike-voice'
          value: 'en-US-DavisNeural'
        }
        {
          name: 'flask-secret-key'
          value: base64(uniqueString(resourceGroup().id, 'flask-secret'))
        }
        {
          name: 'azure-ad-b2c-tenant-id'
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'azure-ad-b2c-client-id'
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'azure-ad-b2c-client-secret'
          value: 'PLACEHOLDER_WILL_BE_SET_MANUALLY'
        }
        {
          name: 'azure-ad-b2c-policy-name'
          value: 'B2C_1_signupsignin'
        }
      ]
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentity.id
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
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
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
          ]
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 5000
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 5000
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '5'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output storageAccountName string = storageAccount.name
output managedIdentityId string = managedIdentity.id
