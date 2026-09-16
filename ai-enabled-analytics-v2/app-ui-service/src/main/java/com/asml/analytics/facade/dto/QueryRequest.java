package com.asml.analytics.facade.dto;

import java.util.Map;

/**
 * Request body for WaferDataService.query() (.github/copilot-instructions.md
 * `## 8`).
 */
public class QueryRequest {

    private String workspaceId;
    private String table;
    private Map<String, Object> filters;

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

    public Map<String, Object> getFilters() {
        return filters;
    }

    public void setFilters(Map<String, Object> filters) {
        this.filters = filters;
    }
}
