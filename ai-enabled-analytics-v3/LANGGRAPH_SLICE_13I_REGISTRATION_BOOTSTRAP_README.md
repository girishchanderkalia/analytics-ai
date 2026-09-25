# Slice 13I: Registration bootstrap

Adds validated startup registration for Slice 13G packages.

## Configure

```bash
export AGENT_PACKAGE_MANIFESTS="app-ui/opo-monitoring/agent/agent-package.yaml"
```

## Focused tests

```bash
PYTHONPATH=".;./agent-framework/agent-runtime" \
python run_pytest.py --import-mode=importlib \
  agent-framework/agent-registration-bootstrap/tests -v --tb=short
```
