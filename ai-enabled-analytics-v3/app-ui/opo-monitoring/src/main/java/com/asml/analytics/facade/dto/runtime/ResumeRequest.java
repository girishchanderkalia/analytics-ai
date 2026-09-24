package com.asml.analytics.facade.dto.runtime;

import java.util.Map;

public record ResumeRequest(
        String interruptId,
        Object value,
        Integer expectedVersion,
        Map<String, Object> applicationContext) {
}
