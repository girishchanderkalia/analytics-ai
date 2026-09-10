package com.analytics.agent.service.impl;

import com.analytics.agent.model.Filters;
import com.analytics.agent.service.WorkspaceService;
import org.springframework.stereotype.Service;

import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class WorkspaceServiceImpl implements WorkspaceService {

    // workspaceId -> applied filters (in-memory stub)
    private final ConcurrentHashMap<String, Filters> workspaces = new ConcurrentHashMap<>();

    @Override
    public String createWorkspace() {
        // ConcurrentHashMap rejects null values, so the entry is created only once
        // filters arrive
        return "WS-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    @Override
    public void addFilters(String workspaceId, Filters filters) {
        workspaces.put(workspaceId, filters);
    }
}
