package com.analytics.agent.service;

import com.analytics.agent.model.QueryRequest;
import com.analytics.agent.model.WaferResult;

public interface WaferDataService {
    WaferResult query(QueryRequest request);
}
