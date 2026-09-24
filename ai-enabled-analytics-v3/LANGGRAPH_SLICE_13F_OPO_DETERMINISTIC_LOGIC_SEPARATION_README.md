# Slice 13F: OPO deterministic logic separation

Separates pure OPO calculations from data access:

- Trend row grouping and filtering
- Baseline and absolute-threshold analysis
- Outlier selection
- Wafer row normalization
- Anomalous wafer selection
- Edge-versus-center spatial classification

The package accepts data already retrieved through the BFF Foundation client or
through MCP tools. It has no platform imports.

## Test

```bash
python -m pip install -e ./opo-deterministic-logic
python -m pytest opo-deterministic-logic/tests -v --tb=short
```
