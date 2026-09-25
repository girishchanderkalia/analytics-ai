#!/usr/bin/env bash
set -euo pipefail

python -m pip install -e ./integration-tests

python -m pytest   integration-tests/tests   -m "smoke or deterministic"   -v   --tb=short

if [[ "${RUN_AGENT_E2E:-false}" == "true" ]]; then
  python -m pytest     integration-tests/tests/test_agent_runtime_path.py     -v     --tb=short
fi
