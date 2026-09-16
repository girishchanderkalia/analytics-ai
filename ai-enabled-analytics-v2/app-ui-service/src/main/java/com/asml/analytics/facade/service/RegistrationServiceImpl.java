package com.asml.analytics.facade.service;

import com.asml.analytics.facade.client.WorkflowRuntimeClient;
import com.asml.analytics.facade.dto.RegistrationRequest;
import com.asml.analytics.facade.dto.RegistrationStatus;
import org.springframework.stereotype.Service;

@Service
public class RegistrationServiceImpl implements RegistrationService {

    private final WorkflowRuntimeClient client;

    public RegistrationServiceImpl(WorkflowRuntimeClient client) {
        this.client = client;
    }

    @Override
    public RegistrationStatus register(RegistrationRequest request) {
        return client.register(request.getWorkspaceId(), request.getDataset(), request.getTable());
    }
}
