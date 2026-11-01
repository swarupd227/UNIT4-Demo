// Migration Studio on Azure. See docs/AZURE_DEPLOYMENT.md.
//
// Only the web app has a public address, and it has no sign-in. The API and Postgres are reachable
// from inside the virtual network only. With an empty imageTag this deploys the foundation alone,
// because the apps cannot start until their images are in the registry.
//
// Nothing here assigns a role, so a Contributor can deploy it. The apps read their secrets from Key
// Vault through an access policy, and those secrets include the registry and storage keys.

targetScope = 'resourceGroup'

param location string = 'uksouth'
param imageTag string = ''
param postgresSku string = 'Standard_B2s'

@secure()
param postgresAdminPassword string

var suffix = uniqueString(resourceGroup().id)
var deployApps = !empty(imageTag)
var postgresUser = 'studio'
var blobContainer = 'studio'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-studio'
  location: location
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-studio'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-studio'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'crstudio${suffix}'
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: true }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: 'vnet-studio'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.40.0.0/16'] }
    subnets: [
      {
        name: 'apps'
        properties: {
          addressPrefix: '10.40.0.0/23'
          delegations: [{ name: 'apps', properties: { serviceName: 'Microsoft.App/environments' } }]
        }
      }
      {
        name: 'postgres'
        properties: {
          addressPrefix: '10.40.2.0/24'
          delegations: [
            { name: 'postgres', properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' } }
          ]
        }
      }
    ]
  }
}

resource postgresDns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'studio-${suffix}.private.postgres.database.azure.com'
  location: 'global'
}

resource postgresDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: postgresDns
  name: 'vnet-studio'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: { id: vnet.id }
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: 'psql-studio-${suffix}'
  location: location
  sku: { name: postgresSku, tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: postgresUser
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/postgres'
      privateDnsZoneArmResourceId: postgresDns.id
    }
  }
  dependsOn: [postgresDnsLink]
}

// The first migration creates the vector extension, which Azure refuses unless it is allow-listed.
resource postgresExtensions 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-12-01-preview' = {
  parent: postgres
  name: 'azure.extensions'
  properties: { value: 'VECTOR', source: 'user-override' }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: 'studio'
  properties: { charset: 'UTF8', collation: 'en_GB.utf8' }
  dependsOn: [postgresExtensions]
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'ststudio${suffix}'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: blobContainer
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-studio-${suffix}'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: false
    softDeleteRetentionInDays: 7
    accessPolicies: [
      {
        tenantId: tenant().tenantId
        objectId: identity.properties.principalId
        permissions: { secrets: ['get'] }
      }
    ]
  }
}

resource databaseUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: {
    value: 'postgresql+psycopg://${postgresUser}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDatabase.name}?sslmode=require'
  }
}

resource registryPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'registry-password'
  properties: { value: registry.listCredentials().passwords[0].value }
}

resource storageConnection 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'storage-connection'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
  }
}

resource appEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-studio'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: { infrastructureSubnetId: '${vnet.id}/subnets/apps', internal: false }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
  }
}

var identityBlock = {
  type: 'UserAssigned'
  userAssignedIdentities: { '${identity.id}': {} }
}
var registries = [
  {
    server: registry.properties.loginServer
    username: registry.name
    passwordSecretRef: 'registry-password'
  }
]
var apiImage = '${registry.properties.loginServer}/studio-api:${imageTag}'
var registrySecret = {
  name: 'registry-password'
  keyVaultUrl: registryPassword.properties.secretUri
  identity: identity.id
}
var apiSecrets = [
  registrySecret
  { name: 'database-url', keyVaultUrl: databaseUrl.properties.secretUri, identity: identity.id }
  { name: 'storage-connection', keyVaultUrl: storageConnection.properties.secretUri, identity: identity.id }
]
var apiEnv = [
  { name: 'STUDIO_DATABASE_URL', secretRef: 'database-url' }
  { name: 'STUDIO_LLM_MODE', value: 'replay' }
  { name: 'STUDIO_BLOB_CONNECTION_STRING', secretRef: 'storage-connection' }
  { name: 'STUDIO_BLOB_CONTAINER', value: blobContainer }
  { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
]

// One replica of each, always on: the demo has one shared case, and no cold start on stage.
resource api 'Microsoft.App/containerApps@2024-03-01' = if (deployApps) {
  name: 'ca-studio-api'
  location: location
  identity: identityBlock
  properties: {
    environmentId: appEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: false, targetPort: 8000, transport: 'http' }
      registries: registries
      secrets: apiSecrets
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: apiEnv
          probes: [
            {
              type: 'Startup'
              httpGet: { path: '/healthz', port: 8000 }
              periodSeconds: 5
              failureThreshold: 36
            }
            { type: 'Liveness', httpGet: { path: '/healthz', port: 8000 }, periodSeconds: 15 }
            { type: 'Readiness', httpGet: { path: '/readyz', port: 8000 }, periodSeconds: 10 }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
  dependsOn: [container]
}

resource web 'Microsoft.App/containerApps@2024-03-01' = if (deployApps) {
  name: 'ca-studio-web'
  location: location
  identity: identityBlock
  properties: {
    environmentId: appEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: true, targetPort: 8080, transport: 'auto' }
      registries: registries
      secrets: [registrySecret]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: '${registry.properties.loginServer}/studio-web:${imageTag}'
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [{ name: 'API_UPSTREAM', value: 'https://${api!.properties.configuration.ingress.fqdn}' }]
          probes: [
            { type: 'Liveness', httpGet: { path: '/healthz', port: 8080 }, periodSeconds: 15 }
            { type: 'Readiness', httpGet: { path: '/healthz', port: 8080 }, periodSeconds: 10 }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
}

// Started by hand, because it rebuilds the whole estate. It runs inside the network to reach Postgres.
resource seed 'Microsoft.App/jobs@2024-03-01' = if (deployApps) {
  name: 'caj-studio-seed'
  location: location
  identity: identityBlock
  properties: {
    environmentId: appEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 1800
      replicaRetryLimit: 0
      manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
      registries: registries
      secrets: apiSecrets
    }
    template: {
      containers: [
        {
          name: 'seed'
          image: apiImage
          command: ['python', '-m', 'data.generator.main', '--load']
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: apiEnv
        }
      ]
    }
  }
  dependsOn: [api]
}

output registryName string = registry.name
output registryServer string = registry.properties.loginServer
output webUrl string = deployApps ? 'https://${web!.properties.configuration.ingress.fqdn}' : ''
