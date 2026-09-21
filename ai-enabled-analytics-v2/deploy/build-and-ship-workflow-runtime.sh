#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

REGISTRY="${REGISTRY:-repo.cluster.local:5443}"
NAMESPACE="${NAMESPACE:-ai-agents}"
IMAGE_NAME="${IMAGE_NAME:-analytics-workflow-runtime}"
IMAGE_TAG="${IMAGE_TAG:-$(date -u +%Y%m%d-%H%M%S)}"
IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
DOCKERFILE="ai-enabled-analytics-v2/deploy/Dockerfile.workflow-runtime"
MANIFEST="ai-enabled-analytics-v2/deploy/k8s/workflow-runtime.yaml"
APP_MODULE="${APP_MODULE:-ApplicationUI.analytics_agents.opo_monitoring_service.api:app}"
PUSH="${PUSH:-true}"
APPLY="${APPLY:-true}"
VERIFY="${VERIFY:-true}"
REGENERATE_SCHEMAS="${REGENERATE_SCHEMAS:-true}"

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

if [[ "$APPLY" == "true" || "$VERIFY" == "true" ]]; then
  command -v kubectl >/dev/null 2>&1 || fail "kubectl is required when APPLY or VERIFY is true"
fi
if command -v docker >/dev/null 2>&1 && docker version >/dev/null 2>&1; then
  CONTAINER_TOOL="docker"
elif command -v podman >/dev/null 2>&1 && podman info >/dev/null 2>&1; then
  CONTAINER_TOOL="podman"
else
  fail "a reachable Docker or Podman engine is required"
fi

[[ -f "$DOCKERFILE" ]] || fail "missing $DOCKERFILE"
[[ -f "$MANIFEST" ]] || fail "missing $MANIFEST"
[[ -f requirements.txt ]] || fail "missing requirements.txt"
[[ -d AnalyticsFoundation ]] || fail "missing AnalyticsFoundation source"
[[ -d ApplicationUI ]] || fail "missing ApplicationUI source"
[[ -d ai-enabled-analytics-v2/agent_runtime ]] || fail "missing agent_runtime source"
[[ -d ai-enabled-analytics-v2/ai_Agents ]] || fail "missing ai_Agents definitions"

if [[ "$REGENERATE_SCHEMAS" == "true" ]]; then
  if [[ -x .venv/Scripts/python.exe ]]; then
    PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
  elif [[ -x .venv/bin/python ]]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON=python
  else
    fail "Python is required to regenerate model schemas"
  fi
  printf 'Regenerating Markdown-derived schemas\n'
  (cd ai-enabled-analytics-v2 && "$PYTHON" contracts/generate_model_schemas.py)
fi

printf 'Building %s with %s\n' "$IMAGE" "$CONTAINER_TOOL"
"$CONTAINER_TOOL" build \
  --build-arg "APP_MODULE=$APP_MODULE" \
  -f "$DOCKERFILE" \
  -t "$IMAGE" \
  .

if [[ "$PUSH" == "true" ]]; then
  printf 'Pushing %s\n' "$IMAGE"
  "$CONTAINER_TOOL" push "$IMAGE"
fi

if [[ "$APPLY" == "true" ]]; then
  kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || fail "namespace $NAMESPACE does not exist"
  rendered_manifest="$(sed "s|IMAGE_PLACEHOLDER|$IMAGE|g" "$MANIFEST")"
  printf '%s\n' "$rendered_manifest" | kubectl apply -f -
  kubectl -n "$NAMESPACE" rollout status deployment/analytics-workflow-runtime --timeout=180s
fi

if [[ "$VERIFY" == "true" ]]; then
  kubectl -n "$NAMESPACE" get pods -l app.kubernetes.io/name=analytics-workflow-runtime -o wide
  kubectl -n "$NAMESPACE" get deployment analytics-workflow-runtime \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
  printf '\n'
fi

printf 'Completed workflow-runtime artifact: %s\n' "$IMAGE"
