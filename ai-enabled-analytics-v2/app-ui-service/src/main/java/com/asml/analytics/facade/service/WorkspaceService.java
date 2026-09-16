package com.asml.analytics.facade.service;

import com.asml.analytics.facade.dto.Filters;

/** Per .github/copilot-instructions.md `## 8`. */
public interface WorkspaceService {
    String createWorkspace();

    void addFilters(String workspaceId, Filters filters);
}
