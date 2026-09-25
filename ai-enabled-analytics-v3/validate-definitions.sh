#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "${ROOT}/agent-framework/agent-runtime/execution/validate_agent.py" \
  --repository-root "${ROOT}"
