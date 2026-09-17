package com.asml.analytics.facade.service;

import com.asml.analytics.facade.dto.QueryRequest;
import com.asml.analytics.facade.dto.WaferResult;

/** Per .github/copilot-instructions.md `## 8`. */
public interface WaferDataService {
    WaferResult query(QueryRequest request);
}
