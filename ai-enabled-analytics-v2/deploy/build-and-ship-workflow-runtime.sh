#!/usr/bin/env bash
# Build and ship the Python workflow runtime image to the cluster, following
# the repo's standard pattern (confirmed against this cluster: bastion has
# podman, not docker; nodes pull from the internal repo.cluster.local:5443
# registry):
#   docker build -t <image> .
#   docker save -o <tar> <image>
#   scp <tar> fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
#   ssh ... podman load < <tar> && podman tag <image> repo.cluster.local:5443/<name> && podman push repo.cluster.local:5443/<name>
#
# Must be run from the repository root's build context; see ../Dockerfile for why.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

IMAGE="${IMAGE:-iact/analytics-workflow-runtime:latest}"
REGISTRY_IMAGE="${REGISTRY_IMAGE:-repo.cluster.local:5443/ai-agents/analytics-workflow-runtime:latest}"
TAR_NAME="${TAR_NAME:-analytics-workflow-runtime.tar}"
REMOTE_HOST="${REMOTE_HOST:-fa-VCP@ics027036188.ics-eu-1.asml.com}"
REMOTE_DIR="${REMOTE_DIR:-/home/fa-VCP/}"

cd "$REPO_ROOT"
docker build -f ai-enabled-analytics-v2/Dockerfile -t "$IMAGE" .
docker save -o "ai-enabled-analytics-v2/deploy/$TAR_NAME" "$IMAGE"
scp "ai-enabled-analytics-v2/deploy/$TAR_NAME" "${REMOTE_HOST}:${REMOTE_DIR}"
rm -f "ai-enabled-analytics-v2/deploy/$TAR_NAME"

ssh "$REMOTE_HOST" \
  "podman load -i ${REMOTE_DIR}${TAR_NAME} && \
   podman tag ${IMAGE} ${REGISTRY_IMAGE} && \
   podman push ${REGISTRY_IMAGE} && \
   rm -f ${REMOTE_DIR}${TAR_NAME}"

echo "Pushed ${REGISTRY_IMAGE}. Next: kubectl apply -n ai-agents -f - < ../deploy/k8s/workflow-runtime.yaml (via the SSH host)."
