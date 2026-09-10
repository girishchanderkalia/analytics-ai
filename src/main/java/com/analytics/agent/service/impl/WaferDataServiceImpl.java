package com.analytics.agent.service.impl;

import com.analytics.agent.model.QueryRequest;
import com.analytics.agent.model.WaferResult;
import com.analytics.agent.service.WaferDataService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class WaferDataServiceImpl implements WaferDataService {

    @Override
    public WaferResult query(QueryRequest request) {
        // Stub: return representative wafer-level rows for the filtered machine/product
        List<Map<String, Object>> rows = List.of(
            Map.of("waferId", "W001", "machine", "NXE3600", "product", "ProductA", "yieldPct", 72.3, "defectDensity", 0.42),
            Map.of("waferId", "W002", "machine", "NXE3600", "product", "ProductA", "yieldPct", 69.1, "defectDensity", 0.51),
            Map.of("waferId", "W003", "machine", "NXE3600", "product", "ProductA", "yieldPct", 71.8, "defectDensity", 0.44),
            Map.of("waferId", "W004", "machine", "NXE3600", "product", "ProductA", "yieldPct", 55.2, "defectDensity", 1.23),
            Map.of("waferId", "W005", "machine", "NXE3600", "product", "ProductA", "yieldPct", 56.0, "defectDensity", 1.18)
        );
        String summary = "5 wafers queried for workspace %s on table %s. "
                + "2 wafers (W004, W005) show elevated defect density > 1.0, "
                + "correlated with yield below 57%%.".formatted(request.workspaceId(), request.table());
        return new WaferResult(rows, summary);
    }
}
