# Fixed Capability Dispatcher Bootstrap

This patch adds the next fixed-framework bootstrap slice after Model Gateway
wiring. It does not introduce a second capability registry or select platform
adaptors through environment variables.

The adapter delegates the complete governance context to the existing
Capability Registry:

- logical capability ID
- workflow state
- granted permissions
- approved side-effect capabilities

The existing declarative tools-and-capabilities definition remains the source
for capability names, permission requirements, side-effect flags, and approval
policy.

## Validate

```bash
python -m compileall agent-runtime tests -q
PYTHONPATH=".:./agent-runtime" python -m pytest tests/test_capability_dispatcher_bootstrap.py -v
PYTHONPATH=".:./agent-runtime" python -m pytest tests -q
```
