package com.asml.analytics.facade.dto;

import java.util.List;
import java.util.Map;

/**
 * Response shape for POST /workspaces/{id}/wafers/query, per the workflow
 * runtime OpenAPI contract.
 */
public class WaferResult {

    private String workspaceId;
    private String table;
    private List<Map<String, Object>> rows;
    private List<String> anomalousWafers;

    public String getWorkspaceId() {
        return workspaceId;
    }

    public void setWorkspaceId(String workspaceId) {
        this.workspaceId = workspaceId;
    }

    public String getTable() {
        return table;
    }

    public void setTable(String table) {
        this.table = table;
    }

    public List<Map<String, Object>> getRows() {
        return rows;
    }

    public void setRows(List<Map<String, Object>> rows) {
        this.rows = rows;
    }

    public List<String> getAnomalousWafers() {
        return anomalousWafers;
    }

    public void setAnomalousWafers(List<String> anomalousWafers) {
        this.anomalousWafers = anomalousWafers;
    }
}
