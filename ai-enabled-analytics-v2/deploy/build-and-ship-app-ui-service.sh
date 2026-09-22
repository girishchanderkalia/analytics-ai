#!/usr/bin/env bash
# Build and ship the app-ui-service image to the cluster, following the
# repo's standard pattern (confirmed against this cluster: bastion has podman,
# not docker; nodes pull from the internal repo.cluster.local:5443 registry):
#   mvn clean package
#   docker build -t <image> .
#   docker save -o <tar> <image>
#   scp <tar> fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
#   ssh ... podman load < <tar> && podman tag <image> repo.cluster.local:5443/<name> && podman push repo.cluster.local:5443/<name>
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FACADE_DIR="$SCRIPT_DIR/../app-ui-service"

IMAGE="${IMAGE:-iact/app-ui-service:latest}"
REGISTRY_IMAGE="${REGISTRY_IMAGE:-repo.cluster.local:5443/ai-agents/app-ui-service:latest}"
TAR_NAME="${TAR_NAME:-app-ui-service.tar}"
REMOTE_HOST="${REMOTE_HOST:-fa-VCP@ics027036188.ics-eu-1.asml.com}"
REMOTE_DIR="${REMOTE_DIR:-/home/fa-VCP/}"

cd "$FACADE_DIR"
mvn clean package
docker build -t "$IMAGE" .
docker save -o "$TAR_NAME" "$IMAGE"
scp "$TAR_NAME" "${REMOTE_HOST}:${REMOTE_DIR}"
rm -f "$TAR_NAME"

ssh "$REMOTE_HOST" \
  "podman load -i ${REMOTE_DIR}${TAR_NAME} && \
   podman tag ${IMAGE} ${REGISTRY_IMAGE} && \
   podman push ${REGISTRY_IMAGE} && \
   rm -f ${REMOTE_DIR}${TAR_NAME}"

echo "Pushed ${REGISTRY_IMAGE}. Next: kubectl apply -n ai-agents -f - < ../deploy/k8s/app-ui-service.yaml (via the SSH host)."
