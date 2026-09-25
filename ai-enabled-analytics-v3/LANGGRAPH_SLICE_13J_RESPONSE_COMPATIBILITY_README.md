# Slice 13J: Response compatibility

Preserves the legacy `/chat`, `/resume`, and `/threads/{thread_id}` response
shapes. The field names and status precedence are based on the existing OPO BFF
contract.

## Focused tests

```bash
PYTHONPATH=".;./agent-framework/agent-runtime" \
python run_pytest.py --import-mode=importlib \
  app-ui/opo-monitoring/opo-monitoring-service/opo-response-compatibility/tests -v --tb=short
```
