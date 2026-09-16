#!/usr/bin/env bash
# Ship the stock PostgreSQL image to the cluster using the same podman
# load/tag/push shape as the app images (no build step - pulled, not built).
# Only needed if the cluster's containerd can't pull postgres:16-alpine
# directly from Docker Hub; otherwise reference it as-is in
# deploy/k8s/postgres.yaml.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

IMAGE="${IMAGE:-postgres:16-alpine}"
REGISTRY_IMAGE="${REGISTRY_IMAGE:-repo.cluster.local:5443/ai-agents/postgres:16-alpine}"
TAR_NAME="${TAR_NAME:-postgres-16-alpine.tar}"
REMOTE_HOST="${REMOTE_HOST:-fa-VCP@ics027036188.ics-eu-1.asml.com}"
REMOTE_DIR="${REMOTE_DIR:-/home/fa-VCP/}"

docker pull "$IMAGE"
docker save -o "$SCRIPT_DIR/$TAR_NAME" "$IMAGE"
scp "$SCRIPT_DIR/$TAR_NAME" "${REMOTE_HOST}:${REMOTE_DIR}"
rm -f "$SCRIPT_DIR/$TAR_NAME"

ssh "$REMOTE_HOST" \
  "podman load -i ${REMOTE_DIR}${TAR_NAME} && \
   podman tag ${IMAGE} ${REGISTRY_IMAGE} && \
   podman push ${REGISTRY_IMAGE} && \
   rm -f ${REMOTE_DIR}${TAR_NAME}"

echo "Pushed ${REGISTRY_IMAGE}. Next: kubectl apply -n ai-agents -f - < ../deploy/k8s/postgres.yaml (via the SSH host)."
