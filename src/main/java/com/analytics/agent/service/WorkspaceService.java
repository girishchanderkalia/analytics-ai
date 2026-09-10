package com.analytics.agent.service;

import com.analytics.agent.model.Filters;

public interface WorkspaceService {
    String createWorkspace();
    void addFilters(String workspaceId, Filters filters);
}
