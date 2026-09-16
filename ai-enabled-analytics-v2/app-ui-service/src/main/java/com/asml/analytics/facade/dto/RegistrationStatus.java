package com.asml.analytics.facade.dto;

/**
 * Response shape for POST /workspaces/{id}/register, per the workflow runtime
 * OpenAPI contract.
 */
public class RegistrationStatus {

    private String status;
    private String workspaceId;
    private Integer progressPct;
    private String table;

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getWorkspaceId() {
        return workspaceId;
    }

    public void setWorkspaceId(String workspaceId) {
        this.workspaceId = workspaceId;
    }

    public Integer getProgressPct() {
        return progressPct;
    }

    public void setProgressPct(Integer progressPct) {
        this.progressPct = progressPct;
    }

    public String getTable() {
        return table;
    }

    public void setTable(String table) {
        this.table = table;
    }
}
