# Deploying from Azure Cloud Shell

Paste these blocks into Cloud Shell in the Azure portal, using **Bash**, not PowerShell. Every block assumes a fresh shell, so each one sets the subscription and its own values first. Run steps 1 to 8 once, in order. After that, use [Deploying a change](#deploying-a-change).

Nothing here has been run against a real subscription yet, so expect to fix something on the first pass. The [problems table](#if-something-fails) lists the likely ones.

## Before you start

Blocks that need the code get it from https://github.com/swarupd227/UNIT4-Demo: they clone the repository if the shell doesn't have it, then pull the latest `main`. So push your changes before you deploy them. Cloud Shell has no Docker, so Azure builds the images from that code.

You will need to keep two secrets from step 2 in your password manager. Cloud Shell won't remember them.

## Step 1: Prepare the subscription

This registers the Azure services the demo uses and creates the resource group. Registration can take a few minutes.

```bash
az account set --subscription "Microsoft Azure Sponsorship"
az account show --query "{subscription:name, user:user.name}" --output table

for provider in Microsoft.App Microsoft.ContainerRegistry Microsoft.DBforPostgreSQL Microsoft.KeyVault \
  Microsoft.Storage Microsoft.OperationalInsights Microsoft.Insights Microsoft.Network \
  Microsoft.ManagedIdentity; do
  az provider register --namespace "$provider" --wait
done

az group create --name rg-migration-studio --location uksouth --output table
```

## Step 2: Create the sign-in app and the secrets

Run this **once**. Running it again creates a second app. It prints three values: save the app ID, and keep the two secrets in your password manager.

```bash
az account set --subscription "Microsoft Azure Sponsorship"

APP_ID=$(az ad app create --display-name "Migration Studio" --sign-in-audience AzureADMyOrg \
  --enable-id-token-issuance true --query appId --output tsv)
ENTRA_SECRET=$(az ad app credential reset --id "$APP_ID" --display-name deployment \
  --query password --output tsv)
POSTGRES_PASSWORD=$(openssl rand -hex 32)

echo "ENTRA_CLIENT_ID:         $APP_ID"
echo "ENTRA_CLIENT_SECRET:     $ENTRA_SECRET"
echo "POSTGRES_ADMIN_PASSWORD: $POSTGRES_PASSWORD"
```

## Step 3: Deploy the foundation

This creates the network, Postgres, storage, Key Vault and the registry. It takes about 15 minutes, and most of that is Postgres. It asks for the three values from step 2, and what you type stays hidden.

The braces make the shell read the whole paste before it asks for anything. If nothing happens after pasting, press Enter.

```bash
{
az account set --subscription "Microsoft Azure Sponsorship"
[ -d ~/UNIT4-Demo ] || git clone https://github.com/swarupd227/UNIT4-Demo.git ~/UNIT4-Demo
cd ~/UNIT4-Demo && git pull --ff-only

read -rsp "ENTRA_CLIENT_ID: " ENTRA_CLIENT_ID && echo
read -rsp "ENTRA_CLIENT_SECRET: " ENTRA_CLIENT_SECRET && echo
read -rsp "POSTGRES_ADMIN_PASSWORD: " POSTGRES_ADMIN_PASSWORD && echo
export ENTRA_CLIENT_ID ENTRA_CLIENT_SECRET POSTGRES_ADMIN_PASSWORD
export AZURE_LOCATION=uksouth IMAGE_TAG=""

az deployment group create --name foundation --resource-group rg-migration-studio \
  --parameters infra/main.bicepparam --query properties.provisioningState --output tsv
}
```

It should print `Succeeded`.

## Step 4: Build the images

Azure builds both images in the registry. This takes about 10 minutes.

```bash
az account set --subscription "Microsoft Azure Sponsorship"
[ -d ~/UNIT4-Demo ] || git clone https://github.com/swarupd227/UNIT4-Demo.git ~/UNIT4-Demo
cd ~/UNIT4-Demo && git pull --ff-only

REGISTRY=$(az acr list --resource-group rg-migration-studio --query "[0].name" --output tsv)
TAG=$(git rev-parse --short=12 HEAD)

az acr build --registry "$REGISTRY" --image "studio-api:$TAG" --target production \
  --file apps/api/Dockerfile . && \
az acr build --registry "$REGISTRY" --image "studio-web:$TAG" apps/web && \
echo "Built $TAG"
```

## Step 5: Deploy the apps

This deploys the newest images. It asks for the same three values.

```bash
{
az account set --subscription "Microsoft Azure Sponsorship"
[ -d ~/UNIT4-Demo ] || git clone https://github.com/swarupd227/UNIT4-Demo.git ~/UNIT4-Demo
cd ~/UNIT4-Demo && git pull --ff-only

read -rsp "ENTRA_CLIENT_ID: " ENTRA_CLIENT_ID && echo
read -rsp "ENTRA_CLIENT_SECRET: " ENTRA_CLIENT_SECRET && echo
read -rsp "POSTGRES_ADMIN_PASSWORD: " POSTGRES_ADMIN_PASSWORD && echo
REGISTRY=$(az acr list --resource-group rg-migration-studio --query "[0].name" --output tsv)
IMAGE_TAG=$(az acr repository show-tags --name "$REGISTRY" --repository studio-web \
  --orderby time_desc --top 1 --output tsv)
export ENTRA_CLIENT_ID ENTRA_CLIENT_SECRET POSTGRES_ADMIN_PASSWORD IMAGE_TAG
export AZURE_LOCATION=uksouth

echo "Deploying $IMAGE_TAG"
az deployment group create --name "apps-$IMAGE_TAG" --resource-group rg-migration-studio \
  --parameters infra/main.bicepparam --query properties.outputs.webUrl.value --output tsv
}
```

It prints the site URL.

## Step 6: Turn on sign-in and add yourself

This allows the site's address to sign in, limits the app to named people, and adds you. Paste your app ID into the first line.

```bash
az account set --subscription "Microsoft Azure Sponsorship"
APP_ID="<paste ENTRA_CLIENT_ID>"

FQDN=$(az containerapp show --name ca-studio-web --resource-group rg-migration-studio \
  --query properties.configuration.ingress.fqdn --output tsv)
az ad app update --id "$APP_ID" --web-redirect-uris "https://$FQDN/.auth/login/aad/callback"

SP_ID=$(az ad sp show --id "$APP_ID" --query id --output tsv 2>/dev/null \
  || az ad sp create --id "$APP_ID" --query id --output tsv)
az ad sp update --id "$SP_ID" --set appRoleAssignmentRequired=true

USER_ID=$(az ad signed-in-user show --query id --output tsv)
az rest --method POST --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
  --headers "Content-Type=application/json" \
  --body "{\"principalId\":\"$USER_ID\",\"resourceId\":\"$SP_ID\",\"appRoleId\":\"00000000-0000-0000-0000-000000000000\"}" \
  --output none

echo "Site: https://$FQDN"
```

To add the rest of the demo team, use Microsoft Entra ID > Enterprise applications > Migration Studio > Users and groups.

## Step 7: Load the estate

This starts the seed job and waits for it to finish, which takes a few minutes. It rebuilds everything, so **running it later wipes all decisions**.

```bash
az account set --subscription "Microsoft Azure Sponsorship"

az containerapp job start --name caj-studio-seed --resource-group rg-migration-studio --output none
sleep 20
while true; do
  STATUS=$(az containerapp job execution list --name caj-studio-seed --resource-group rg-migration-studio \
    --query "sort_by(@, &properties.startTime)[-1].properties.status" --output tsv)
  echo "$(date +%T) $STATUS"
  case "$STATUS" in Succeeded|Failed|Stopped) break ;; esac
  sleep 15
done
```

It should end on `Succeeded`.

## Step 8: Check it

The first line should show `200`. The second should show a sign-in address, which proves a signed-out visitor can't get in.

```bash
az account set --subscription "Microsoft Azure Sponsorship"

FQDN=$(az containerapp show --name ca-studio-web --resource-group rg-migration-studio \
  --query properties.configuration.ingress.fqdn --output tsv)
curl --silent --output /dev/null --write-out "health: %{http_code}\n" "https://$FQDN/healthz"
curl --silent --output /dev/null --write-out "signed-out visitor goes to: %{redirect_url}\n" "https://$FQDN/"
echo "Open https://$FQDN"
```

Then open the site in a browser, sign in, and run a full rehearsal. That rehearsal is the Phase 6 exit gate, and the 2-second load limit needs measuring again on Azure.

## Deploying a change

Push your changes to `main`, then run steps 4 and 5. Your data stays as it is, and any database migrations run when the API starts.

## If something fails

| What you see | What it means | What to do |
|---|---|---|
| `LocationIsOfferRestricted`, or a similar region or SKU refusal in step 3 | Sponsorship offers can limit regions and sizes | Change `uksouth` to another region, such as `westeurope`, in steps 3 and 5, and rerun step 3 |
| `TasksOperationsNotAllowed` in step 4 | The subscription doesn't allow registry builds | Use the fallback below |
| `toomanyrequests` in step 4 | Docker Hub limited the build | Wait a while, then rerun step 4 |
| `Insufficient privileges` in step 2 or 6 | Your account can't manage Entra apps | Ask your Entra administrator to run those steps |
| `AuthorizationFailed` on a role assignment in step 3 | You need Owner on the group, not Contributor | Ask a subscription owner for it, then rerun step 3 |
| `AADSTS50105` when signing in | You aren't assigned to the app | Rerun step 6, or add yourself under Users and groups |
| `AADSTS50011` when signing in | The redirect address isn't registered | Rerun step 6 |
| Site shows an error after sign-in, or step 7 ends on `Failed` | The app or the job failed at startup | Run the logs block below |

### Reading the logs

```bash
az account set --subscription "Microsoft Azure Sponsorship"

az containerapp logs show --name ca-studio-api --resource-group rg-migration-studio --tail 60 --type console
az containerapp logs show --name ca-studio-web --resource-group rg-migration-studio --tail 30 --type console
```

### If the registry can't build

Build on your own machine with Docker Desktop instead. First get a short-lived sign-in token in Cloud Shell:

```bash
az account set --subscription "Microsoft Azure Sponsorship"

REGISTRY=$(az acr list --resource-group rg-migration-studio --query "[0].name" --output tsv)
echo "Registry: $REGISTRY.azurecr.io"
az acr login --name "$REGISTRY" --expose-token --query accessToken --output tsv
```

Then ask for help pushing from your machine, or run `docker login` against that registry with the user name `00000000-0000-0000-0000-000000000000` and the token, build with the commands in [infra/deploy.sh](../infra/deploy.sh), and carry on from step 5.

## Shutting it down

The apps and Postgres stay on, so they keep spending while idle. This permanently deletes everything in the group, including all decisions and packs:

```bash
az account set --subscription "Microsoft Azure Sponsorship"

az group delete --name rg-migration-studio --yes --no-wait
```

Key Vault holds its name for 7 days after that, so redeploying into the same group name within a week can fail until the vault is purged.
