package com.asml.analytics.facade.dto;

/**
 * Request body for RegistrationService.register()
 * (.github/copilot-instructions.md `## 8`).
 */
public class RegistrationRequest {

    private String workspaceId;
    private String dataset;
    private String table;

    public String getWorkspaceId() {
        return workspaceId;
    }

    public void setWorkspaceId(String workspaceId) {
        this.workspaceId = workspaceId;
    }

    public String getDataset() {
        return dataset;
    }

    public void setDataset(String dataset) {
        this.dataset = dataset;
    }

    public String getTable() {
        return table;
    }

    public void setTable(String table) {
        this.table = table;
    }
}
