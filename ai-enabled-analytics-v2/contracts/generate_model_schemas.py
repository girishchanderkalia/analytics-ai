#!/usr/bin/env python
"""Regenerate contracts/model/*.schema.json from the Python model contracts.

Run from ai-enabled-analytics-v2/: `python contracts/generate_model_schemas.py`.
Per PLAN.md Phase 5, `agent_runtime/application_agent/contracts.py` is the
source of truth; this script is the only sanctioned way to update the checked-in
schema files. Do not hand-edit the generated `*.schema.json` files.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_runtime.application_agent.contracts import DetectionScope, FindingsSummary, TrendFilters

OUTPUT_DIR = Path(__file__).parent / "model"

MODELS = {"TrendFilters": TrendFilters, "DetectionScope": DetectionScope, "FindingsSummary": FindingsSummary}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"https://asml.com/contracts/model/{name}.schema.json",
            **model.model_json_schema(),
        }
        path = OUTPUT_DIR / f"{name}.schema.json"
        path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
