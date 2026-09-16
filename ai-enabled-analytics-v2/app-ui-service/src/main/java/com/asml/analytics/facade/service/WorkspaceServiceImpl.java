package com.asml.analytics.facade.service;

import com.asml.analytics.facade.client.WorkflowRuntimeClient;
import com.asml.analytics.facade.dto.Filters;
import org.springframework.stereotype.Service;

@Service
public class WorkspaceServiceImpl implements WorkspaceService {

    private final WorkflowRuntimeClient client;

    public WorkspaceServiceImpl(WorkflowRuntimeClient client) {
        this.client = client;
    }

    @Override
    public String createWorkspace() {
        return client.createWorkspace();
    }

    @Override
    public void addFilters(String workspaceId, Filters filters) {
        client.addFilters(workspaceId, filters.getValues());
    }
}
