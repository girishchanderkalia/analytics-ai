package com.asml.analytics.facade.service;

import com.asml.analytics.facade.client.WorkflowRuntimeClient;
import com.asml.analytics.facade.dto.QueryRequest;
import com.asml.analytics.facade.dto.WaferResult;
import org.springframework.stereotype.Service;

@Service
public class WaferDataServiceImpl implements WaferDataService {

    private final WorkflowRuntimeClient client;

    public WaferDataServiceImpl(WorkflowRuntimeClient client) {
        this.client = client;
    }

    @Override
    public WaferResult query(QueryRequest request) {
        return client.queryWafers(request.getWorkspaceId(), request.getTable(), request.getFilters());
    }
}
