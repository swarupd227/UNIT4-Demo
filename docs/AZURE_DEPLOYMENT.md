# Deploying Migration Studio to Azure

This is the reference for Phase 6. For copy-paste commands from the Azure portal, use [the Cloud Shell runbook](AZURE_CLOUD_SHELL.md). Nothing here has been run against a real subscription yet.

## What gets deployed

| Part | Azure service | Notes |
|---|---|---|
| Web | Container Apps, public, no sign-in | nginx serves the app and is the only route to the API |
| API | Container Apps, internal only | Runs database migrations when it starts |
| Seed | Container Apps job, started by hand | Rebuilds the whole estate |
| Database | PostgreSQL Flexible Server 16 | Private to the virtual network, with `vector` allow-listed |
| Files | Blob Storage | Sign-off packs. Managed identity only, shared keys off |
| Secrets | Key Vault | Read by managed identity |
| Images | Container Registry | Pulled by managed identity |
| Telemetry | Application Insights, Log Analytics | Traces from the API, logs from all containers |

The region defaults to UK South. Set `AZURE_LOCATION` to change it. All data is synthetic, and the demo stays in replay mode, so nothing leaves for an LLM provider.

## Access

The site has no sign-in, by decision. Anyone with the URL can open it, switch persona, change decisions, sign the pack, open `/presenter` and reset the workspace. Postgres and the API stay private, so that reach ends at what the app itself allows.

There is one shared case. Two people using the site at the same time will see each other's changes. Reset the workspace from the presenter console before presenting, and share the URL only with people who need it.

## What you need first

- An Azure subscription and a resource group, with Owner on the group. The templates assign roles to the managed identity, so Contributor alone is not enough.
- The steps in [the Cloud Shell runbook](AZURE_CLOUD_SHELL.md), or Azure CLI 2.61 or newer, Docker and Git Bash to use `infra/deploy.sh`.
- The scene recordings, which are kept in Git. Run `npm run record` and commit them if the screens change. The web image refuses to build without all nine.

## Automated deployment

`.github/workflows/ci.yml` runs every check on pull requests. `.github/workflows/deploy.yml` is started by hand from https://github.com/swarupd227/UNIT4-Demo.

To enable deployment, create a GitHub environment called `azure`, plus an Entra identity with Owner on the resource group and a federated credential for that environment. Then set:

| Kind | Names |
|---|---|
| Variables | `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP` |
| Secret | `POSTGRES_ADMIN_PASSWORD` |

## Before presenting on the Azure URL

1. Open the presenter console from the same browser with Ctrl+Alt+P, and reset the workspace.
2. Run a full rehearsal on the Azure URL. This is the Phase 6 exit gate. The 2-second load figure was measured locally, so measure it again here.
3. Keep `npm run demo` ready on the laptop as the fallback.

## Rehearsing the Azure setup locally

`npm run sim` runs the production images with Blob Storage emulated, and with the API reachable only through the web container, on http://localhost:5185. `npm run sim:e2e` runs the browser tests against it, and `npm run sim:stop` removes it. It uses its own data, so the local demo is untouched.

It can't prove anything about managed identity, Key Vault, private networking, Application Insights or Azure's speed.

## Shutting it down

The Container Apps and Postgres keep costing money while idle, because both are set to stay on. Deleting the resource group is permanent. Key Vault keeps its name reserved for 7 days afterwards, so a redeploy into a same-named group within a week can fail until you purge it.
