# Deploying ai-enabled-analytics-v2 to the `ai-agents` namespace

Follows the repo's standard image build/ship pattern
(`.github/copilot-instructions.md` `## 9 Deployment`): build locally, save to a
tar, `scp` it to the cluster host (reachable only via SSH), then make the image
available to the cluster and `kubectl apply`. **Nothing in this folder runs
automatically outside a script you invoke yourself** - review before pushing
anything to a shared cluster.

## Cluster specifics (confirmed by deploying)

- The bastion (`fa-VCP@ics027036188.ics-eu-1.asml.com`) has **podman**, not
  docker; cluster nodes run **containerd** (RKE2), not docker either.
- Images reach the cluster via the internal registry `repo.cluster.local:5443`
  (already used by other workloads on this cluster). No registry login was
  needed to push from the bastion.
- `imagePullPolicy: Always` is required on the app Deployments - nodes cache
  images by tag, so re-pushing `latest` with new content is invisible to a node
  that already pulled that tag under `IfNotPresent`.

## Images

| Image | Built from | Script | Registry destination |
|---|---|---|---|
| `iact/app-ui-service:latest` | `app-ui-service/` (`mvn clean package` then `docker build`) | `build-and-ship-app-ui-service.sh` | `repo.cluster.local:5443/ai-agents/app-ui-service:latest` |
| `iact/analytics-workflow-runtime:latest` | repo root context, `ai-enabled-analytics-v2/Dockerfile` | `build-and-ship-workflow-runtime.sh` | `repo.cluster.local:5443/ai-agents/analytics-workflow-runtime:latest` |
| `postgres:16-alpine` | pulled, not built | `build-and-ship-postgres.sh` | `repo.cluster.local:5443/ai-agents/postgres:16-alpine` |

Each script runs the full chain:

```bash
mvn clean package                                   # app-ui-service only
docker build -t <image> .
docker save -o <image>.tar <image>
scp <image>.tar fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
ssh fa-VCP@... podman load -i ... && podman tag ... && podman push ...
```

## Applying manifests

```bash
scp deploy/k8s/postgres.yaml fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
ssh fa-VCP@ics027036188.ics-eu-1.asml.com kubectl apply -n ai-agents -f /home/fa-VCP/postgres.yaml
```

Apply order: `k8s/postgres.yaml`, then `k8s/workflow-runtime.yaml`, then
`k8s/app-ui-service.yaml` (each depends on the previous one's Service DNS name).

## External access: Istio ingress gateway (not port-forward)

`kubectl port-forward` (used earlier for ad-hoc testing) is unreliable for
anything beyond a quick check - it drops under load or after ~30-60s
(`error creating error stream ...: Timeout occurred`, `broken pipe`). This
cluster has a real, shared Istio ingress Gateway (`istio-system/ingress-prod`)
running on the edge nodes (`asml.com/vcp-node-type=k8s_edge`, e.g.
`ics027032213`), reachable at `http://ics027032213.ics-eu-1.asml.com:8080`
(port **8080**, not 80 - that's the gateway pods' actual `hostPort`; the
in-cluster Service's port 80 is ClusterIP-only). Every other app on this
cluster exposes itself the same way: one shared wildcard-host (`hosts: ["*"]`)
Gateway, disambiguated per app by URL path prefix via a `VirtualService`.

- `k8s/ingress-app-ui-service.yaml` — `app-ui-service` (Java facade) under
  `/ai` (e.g. `http://ics027032213.ics-eu-1.asml.com:8080/ai/trends`),
  prefix stripped via `uriRegexRewrite` before forwarding.
- `k8s/ingress-app-ui.yaml` — the browser UI (still served by
  `analytics-workflow-runtime` today - interim, see PLAN.md) under `/ai-ui`
  (e.g. `.../ai-ui/`), **plus** bare-path routes for `/trends`, `/chat`,
  `/resume`, `/threads/*`, `/sessions/*`, `/static/*`, `/vendor/*` - the
  original UI's JS calls all of these as absolute root paths with no
  awareness of a path prefix, so they have to be claimed on the shared
  wildcard host too. **This is an interim/test convenience, not a long-term
  exposure**: those are fairly generic path names on a multi-tenant shared
  gateway, and a collision check was only done once (see comments in that
  file) - a future unrelated app could legitimately claim one of them later.

Apply the same way as the other manifests:
```bash
scp deploy/k8s/ingress-app-ui-service.yaml deploy/k8s/ingress-app-ui.yaml fa-VCP@ics027036188.ics-eu-1.asml.com:/home/fa-VCP/
ssh fa-VCP@ics027036188.ics-eu-1.asml.com "kubectl apply -f /home/fa-VCP/ingress-app-ui-service.yaml -f /home/fa-VCP/ingress-app-ui.yaml"
```

## Secrets/config created out-of-band (not in these manifests)

- `analytics-postgres-credentials` (`password`, randomly generated) and
  `analytics-postgres-schema` (a ConfigMap of `db/schema.sql`) — see comments
  in `k8s/postgres.yaml`.
- `analytics-workflow-runtime-secrets` (`database-url`, built from the same
  generated password) — see comments in `k8s/workflow-runtime.yaml`.
- Model gateway credentials: `foundation/config.py::get_api_key` uses
  `DefaultAzureCredential`, which needs a managed/workload identity bound to
  the `analytics-workflow-runtime` pod in-cluster; local `az login` does not
  carry over. **Confirmed blocking in practice** (see Status below) — not
  resolved yet.

## Status: deployed and running in `ai-agents`

All three pods are `1/1 Running` with 0 restarts:

```
analytics-postgres            1/1   Running
analytics-workflow-runtime    1/1   Running
app-ui-service                1/1   Running
```

`GET /trends` was verified end-to-end through the facade
(`kubectl exec deploy/app-ui-service -- curl 127.0.0.1:8090/trends`), with
correct field mapping (`lot_id`, `layer_id`, `kpi_value`, ...).

Four issues were found and fixed only by actually deploying (not caught by
`mvn test` / local `docker build`) — see PLAN.md "Phase 6" for the full list:
`mcp` 2.x incompatibility (pinned `mcp<2`), a Key Vault/IMDS call blocking
ASGI startup indefinitely (moved to a background thread), stale node image
cache under a reused tag (`imagePullPolicy: Always`), and a Jackson
camelCase/snake_case field mismatch in `app-ui-service` (global
`SNAKE_CASE` naming strategy).

**Not yet verified:** the model-backed `/chat` investigation flow, because the
workflow runtime still can't authenticate to Key Vault in-cluster (no
managed/workload identity configured). That route will hang per-request (not
crash the pod) until that's resolved. `deploy/k8s/*.yaml` also don't yet set
the `securityContext` fields this cluster's `restricted` Pod Security standard
warns about (non-blocking today).
