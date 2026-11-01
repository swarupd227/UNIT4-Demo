#!/usr/bin/env bash
# Builds the images and deploys them. Used by hand and by .github/workflows/deploy.yml.
# See docs/AZURE_DEPLOYMENT.md for the values this needs and the steps that come first.
set -euo pipefail

: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP}"
: "${ENTRA_CLIENT_ID:?Set ENTRA_CLIENT_ID}"
: "${ENTRA_CLIENT_SECRET:?Set ENTRA_CLIENT_SECRET}"
: "${POSTGRES_ADMIN_PASSWORD:?Set POSTGRES_ADMIN_PASSWORD}"

cd "$(dirname "$0")/.."
tag="$(git rev-parse --short=12 HEAD)"

deploy() {
  IMAGE_TAG="$1" az deployment group create \
    --name main \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --parameters infra/main.bicepparam \
    --query "properties.outputs" --output json
}

output() {
  az deployment group show --resource-group "$AZURE_RESOURCE_GROUP" --name main \
    --query "properties.outputs.$1.value" --output tsv
}

echo "Deploying the foundation"
deploy "" > /dev/null
server="$(output registryServer)"

echo "Pushing images tagged $tag to $server"
az acr login --name "$(output registryName)"
docker build --target production --file apps/api/Dockerfile --tag "$server/studio-api:$tag" .
docker build --tag "$server/studio-web:$tag" apps/web
docker push "$server/studio-api:$tag"
docker push "$server/studio-web:$tag"

echo "Deploying the apps"
deploy "$tag" > /dev/null
url="$(output webUrl)"

# Sign-in is the only thing between the internet and the demo, so prove it is on.
status="$(curl --silent --output /dev/null --write-out '%{http_code}' "$url/healthz")"
location="$(curl --silent --output /dev/null --write-out '%{redirect_url}' "$url/")"
if [ "$status" != "200" ]; then
  echo "Health check failed with $status at $url/healthz" >&2
  exit 1
fi
case "$location" in
  */.auth/login/aad*|https://login.microsoftonline.com/*) ;;
  *)
    echo "The site did not send a signed-out visitor to sign-in. It sent: ${location:-nothing}" >&2
    exit 1
    ;;
esac

echo "Deployed $tag to $url"
echo "Entra redirect URI: $url/.auth/login/aad/callback"
