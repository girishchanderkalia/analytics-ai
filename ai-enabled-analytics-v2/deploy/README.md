# Reusable Workflow Runtime Deployment

The deployment script builds the Python workflow runtime from the repository
root, packages the legacy application service together with the shared
`agent_runtime` and Markdown definitions, pushes an immutable image tag, applies
the Kubernetes manifest, waits for rollout, and verifies the running image.
It also regenerates the checked-in JSON schemas from the Markdown agent
definition before building.

## Build only

```bash
PUSH=false APPLY=false VERIFY=false \
  ./ai-enabled-analytics-v2/deploy/build-and-ship-workflow-runtime.sh
```

Set `REGENERATE_SCHEMAS=false` when schema regeneration is intentionally handled
by a separate CI step.

## Build, push, and deploy

```bash
REGISTRY=repo.cluster.local:5443 \
NAMESPACE=ai-agents \
IMAGE_TAG=$(git rev-parse --short HEAD) \
./ai-enabled-analytics-v2/deploy/build-and-ship-workflow-runtime.sh
```

The script expects the cluster namespace and existing secrets to be present:

- `analytics-postgres-credentials/password`
- `analytics-workflow-runtime-secrets/api-key` (optional for startup, required for model calls)

The default application entrypoint is:

```text
ApplicationUI.analytics_agents.opo_monitoring_service.api:app
```

Override it for a different generic runtime entrypoint with `APP_MODULE`.

The script is fail-fast and does not create namespaces or secrets. Those are
cluster-owned resources and must be provisioned separately.