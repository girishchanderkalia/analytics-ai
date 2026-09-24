package com.asml.analytics.facade.dto.runtime;

import java.util.Map;

public record ChatRequest(
        String applicationId,
        String agentId,
        String agentVersion,
        String conversationId,
        String userId,
        String message,
        Map<String, Object> initialState) {
}
