package com.analytics.agent.model;

import java.util.List;
import java.util.Map;

public record WaferResult(List<Map<String, Object>> rows, String summary) {}
