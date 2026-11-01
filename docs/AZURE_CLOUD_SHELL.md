# Deploying from Azure Cloud Shell

Paste these blocks into Cloud Shell in the Azure portal, using **Bash**, not PowerShell. Every block assumes a fresh shell, so each one sets the subscription and its own values first. Run steps 1 to 6 once, in order. After that, use [Deploying a change](#deploying-a-change).

Blocks that need the code clone https://github.com/swarupd227/UNIT4-Demo, or pull the latest `main` if the shell already has it. Cloud Shell has no Docker, so Azure builds the images from that code.

The site has no sign-in. Anyone with the URL can open it and change its data.

Nothing here has been run against a real subscription yet, so expect to fix something on the first pass.

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

## Step 2: Create the database password

Run this **once**, and keep the password in your password manager. Cloud Shell won't remember it, and steps 3 and 5 ask for it.

```bash
az account set --subscription "Microsoft Azure Sponsorship"
openssl rand -hex 32
```

## Step 3: Deploy the foundation

This creates the network, Postgres, storage, Key Vault and the registry. It takes about 15 minutes, and most of that is Postgres. It asks for the password, and what you type stays hidden. The braces make the shell read the whole paste before it asks. If nothing happens after pasting, press Enter.

```bash
{
az account set --subscription "Microsoft Azure Sponsorship"
[ -d ~/UNIT4-Demo ] || git clone https://github.com/swarupd227/UNIT4-Demo.git ~/UNIT4-Demo
cd ~/UNIT4-Demo && git pull --ff-only

read -rsp "POSTGRES_ADMIN_PASSWORD: " POSTGRES_ADMIN_PASSWORD && echo
export POSTGRES_ADMIN_PASSWORD
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

This deploys the newest images, asks for the password, and prints the site URL.

```bash
{
az account set --subscription "Microsoft Azure Sponsorship"
[ -d ~/UNIT4-Demo ] || git clone https://github.com/swarupd227/UNIT4-Demo.git ~/UNIT4-Demo
cd ~/UNIT4-Demo && git pull --ff-only

read -rsp "POSTGRES_ADMIN_PASSWORD: " POSTGRES_ADMIN_PASSWORD && echo
REGISTRY=$(az acr list --resource-group rg-migration-studio --query "[0].name" --output tsv)
IMAGE_TAG=$(az acr repository show-tags --name "$REGISTRY" --repository studio-web \
  --orderby time_desc --top 1 --output tsv)
export POSTGRES_ADMIN_PASSWORD IMAGE_TAG
export AZURE_LOCATION=uksouth

echo "Deploying $IMAGE_TAG"
az deployment group create --name "apps-$IMAGE_TAG" --resource-group rg-migration-studio \
  --parameters infra/main.bicepparam --query properties.outputs.webUrl.value --output tsv
}
```

## Step 6: Load the data and check the site

This starts the seed job, waits for it, then checks the site. It takes a few minutes. It rebuilds everything, so **running it later wipes all decisions**.

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

FQDN=$(az containerapp show --name ca-studio-web --resource-group rg-migration-studio \
  --query properties.configuration.ingress.fqdn --output tsv)
curl --silent --output /dev/null --write-out "site health: %{http_code}\n" "https://$FQDN/healthz"
curl --silent --output /dev/null --write-out "case data: %{http_code}\n" "https://$FQDN/api/case"
echo "Open https://$FQDN"
```

It should end on `Succeeded`, then `200` twice. Then open the site and run a full rehearsal. That rehearsal is the Phase 6 exit gate, and the 2-second load limit needs measuring again on Azure.

## Deploying a change

Push your changes to `main`, then run steps 4 and 5. Your data stays as it is, and any database migrations run when the API starts.

## If something fails

| What you see | What it means | What to do |
|---|---|---|
| `LocationIsOfferRestricted`, or a similar region or SKU refusal in step 3 | Sponsorship offers can limit regions and sizes | Change `uksouth` to another region, such as `westeurope`, in steps 3 and 5, and rerun step 3 |
| `TasksOperationsNotAllowed` in step 4 | The subscription doesn't allow registry builds | Use the fallback below |
| `toomanyrequests` in step 4 | Docker Hub limited the build | Wait a while, then rerun step 4 |
| The site shows an error, or step 6 ends on `Failed` | The app or the job failed at startup | Run the logs block below |

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

Then run `docker login` against that registry with the user name `00000000-0000-0000-0000-000000000000` and the token, build with the commands in [infra/deploy.sh](../infra/deploy.sh), and carry on from step 5.

## Shutting it down

The apps and Postgres stay on, so they keep spending while idle. This permanently deletes everything in the group, including all decisions and packs:

```bash
az account set --subscription "Microsoft Azure Sponsorship"

az group delete --name rg-migration-studio --yes --no-wait
```

Key Vault holds its name for 7 days after that, so redeploying into the same group name within a week can fail until the vault is purged.
