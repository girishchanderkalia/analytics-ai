package com.asml.analytics.facade.dto.runtime;

import java.util.Map;

public record RuntimeResponse(
        String conversationId,
        String applicationId,
        String agentId,
        String agentVersion,
        String status,
        Integer version,
        Map<String, Object> state,
        Map<String, Object> interrupt) {
}
