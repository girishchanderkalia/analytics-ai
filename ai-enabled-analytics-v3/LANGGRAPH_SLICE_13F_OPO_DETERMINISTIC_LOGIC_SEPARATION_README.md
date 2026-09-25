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
python -m pip install -e ./app-ui/opo-monitoring/opo-monitoring-service/opo-deterministic-logic
python -m pytest app-ui/opo-monitoring/opo-monitoring-service/opo-deterministic-logic/tests -v --tb=short
```
