# Deploying Migration Studio to Azure

This is the reference for Phase 6. For copy-paste commands from the Azure portal, use [the Cloud Shell runbook](AZURE_CLOUD_SHELL.md). The steps below are for deploying from a machine with Docker. Nothing here has been run against a real subscription yet, so treat the first deployment as a test of the runbook as well as of the app.

## What gets deployed

| Part | Azure service | Notes |
|---|---|---|
| Web | Container Apps, public, behind Entra sign-in | nginx serves the app and is the only route to the API |
| API | Container Apps, internal only | Runs database migrations when it starts |
| Seed | Container Apps job, started by hand | Rebuilds the whole estate |
| Database | PostgreSQL Flexible Server 16 | Private to the virtual network, with `vector` allow-listed |
| Files | Blob Storage | Sign-off packs. Managed identity only, shared keys off |
| Secrets | Key Vault | Read by managed identity |
| Images | Container Registry | Pulled by managed identity |
| Telemetry | Application Insights, Log Analytics | Traces from the API, logs from all containers |

The region defaults to UK South. Set `AZURE_LOCATION` to change it. All data is synthetic, and the demo stays in replay mode, so nothing leaves for an LLM provider.

## What sign-in does and does not do

Entra decides who can open the site. Once someone is in, the persona switcher still works as it does locally, because one presenter plays every role. So on Azure the named-role rules are a demonstration of the control, not a security boundary: anyone signed in can act as any persona, reset the demo or sign the pack.

There is one shared case. Two people using the site at the same time will see each other's changes, and a reset affects everyone. Keep the sign-in list to the demo team.

## What you need first

- An Azure subscription and a resource group, with Owner on the group. The templates assign roles to the managed identity, so Contributor alone is not enough.
- Rights to create an app registration in Entra, or someone who can do it for you.
- Azure CLI 2.61 or newer, Docker and Git Bash on the machine that deploys.
- The scene recordings. They are git-ignored, so run `npm run record` first on a fresh checkout. The web image refuses to build without all nine.

## First deployment

Sign in and create the resource group:

```bash
az login
```

```bash
az group create --name rg-migration-studio --location uksouth
```

Create the app registration, then its client secret:

```bash
az ad app create --display-name "Migration Studio" --sign-in-audience AzureADMyOrg --enable-id-token-issuance true --query appId --output tsv
```

```bash
az ad app credential reset --id <app-id> --display-name deployment --query password --output tsv
```

Generate a Postgres password. Use letters and digits only, because it goes into a connection URL:

```bash
openssl rand -hex 32
```

Keep both secrets in your password manager, then set these in Git Bash. Don't put them in a file in this repository:

```bash
export AZURE_RESOURCE_GROUP=rg-migration-studio ENTRA_CLIENT_ID=<app-id>
```

```bash
read -rs ENTRA_CLIENT_SECRET && export ENTRA_CLIENT_SECRET
```

```bash
read -rs POSTGRES_ADMIN_PASSWORD && export POSTGRES_ADMIN_PASSWORD
```

Deploy. This takes about 15 minutes the first time, and most of that is Postgres:

```bash
bash infra/deploy.sh
```

The script ends by checking that `/healthz` answers and that a signed-out visitor is sent to sign-in. It fails the deployment if either check fails. It also prints the site URL and the redirect URI.

Register the redirect URI, then turn on assignment so only named people can sign in:

```bash
az ad app update --id <app-id> --web-redirect-uris <redirect-uri>
```

```bash
az ad sp create --id <app-id>
```

```bash
az ad sp update --id <app-id> --set appRoleAssignmentRequired=true
```

Add the demo team to the app under Entra ID, Enterprise applications, Users and groups.

Load the estate, and wait for the job to show `Succeeded`:

```bash
az containerapp job start --name caj-studio-seed --resource-group rg-migration-studio
```

```bash
az containerapp job execution list --name caj-studio-seed --resource-group rg-migration-studio --output table
```

## Deploying a change

Run `bash infra/deploy.sh` again with the same three variables, or start the **Deploy to Azure** workflow. Migrations run when the API starts, and the data stays as it is. Run the seed job again only when you want the estate rebuilt, because it wipes all decisions.

## Automated deployment

`.github/workflows/ci.yml` runs every check on pull requests. `.github/workflows/deploy.yml` is started by hand. This repository has no remote yet, so neither has run.

To enable deployment, create a GitHub environment called `azure`, plus an Entra identity with Owner on the resource group and a federated credential for that environment. Then set:

| Kind | Names |
|---|---|
| Variables | `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `ENTRA_CLIENT_ID` |
| Secrets | `ENTRA_CLIENT_SECRET`, `POSTGRES_ADMIN_PASSWORD` |

## Before presenting on the Azure URL

1. Sign in shortly before the demo. A session that expires on stage makes API calls fail.
2. Open the presenter console from the same browser, because it needs the same session.
3. Run a full rehearsal on the Azure URL. This is the Phase 6 exit gate. The 2-second load figure was measured locally, so measure it again here.
4. Keep `npm run demo` ready on the laptop as the fallback.

## Rehearsing the Azure setup locally

`npm run sim` runs the production images with Blob Storage emulated, and with the API reachable only through the web container, on http://localhost:5185. `npm run sim:e2e` runs the browser tests against it, and `npm run sim:stop` removes it. It uses its own data, so the local demo is untouched.

It can't prove anything about Entra sign-in, managed identity, Key Vault, private networking, Application Insights or Azure's speed.

## Shutting it down

The Container Apps and Postgres keep costing money while idle, because both are set to stay on. Delete the resource group after the bid if the demo is no longer needed. This is permanent:

```bash
az group delete --name rg-migration-studio
```

Key Vault keeps its name reserved for 7 days after that, so a redeploy into a same-named group within a week can fail until you purge it.
