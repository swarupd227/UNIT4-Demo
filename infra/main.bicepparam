using './main.bicep'

// Read from the environment, so that the password never appears on a command line or in the repository.
param location = readEnvironmentVariable('AZURE_LOCATION', 'uksouth')
param imageTag = readEnvironmentVariable('IMAGE_TAG', '')
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD')
