package com.asml.analytics.facade.service;

import com.asml.analytics.facade.client.WorkflowRuntimeClient;
import com.asml.analytics.facade.dto.TrendResponse;
import org.springframework.stereotype.Service;

@Service
public class TrendServiceImpl implements TrendService {

    private final WorkflowRuntimeClient client;

    public TrendServiceImpl(WorkflowRuntimeClient client) {
        this.client = client;
    }

    @Override
    public TrendResponse getTrends() {
        return client.getTrends();
    }
}
