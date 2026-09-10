package com.analytics.agent.tool;

import com.analytics.agent.model.QueryRequest;
import com.analytics.agent.model.WaferResult;
import com.analytics.agent.service.WaferDataService;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class WaferDataTools {

    private final WaferDataService waferDataService;

    public WaferDataTools(WaferDataService waferDataService) {
        this.waferDataService = waferDataService;
    }

    @Tool(description = """
            Query wafer-level analytical data from StarRocks for a registered workspace table.
            Returns individual wafer rows with yield and defect metrics, plus a summary.
            Only call this after registration status is READY.
            Use the filter field to narrow results (e.g., machine='NXE3600').
            """)
    public WaferResult queryWaferData(
            @ToolParam(description = "Query request with workspaceId, table name, and optional filter expression") QueryRequest request) {
        return waferDataService.query(request);
    }
}
