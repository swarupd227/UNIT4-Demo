using './main.bicep'

// Read from the environment, so that secrets never appear on a command line or in the repository.
param location = readEnvironmentVariable('AZURE_LOCATION', 'uksouth')
param imageTag = readEnvironmentVariable('IMAGE_TAG', '')
param entraClientId = readEnvironmentVariable('ENTRA_CLIENT_ID')
param entraClientSecret = readEnvironmentVariable('ENTRA_CLIENT_SECRET')
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD')
