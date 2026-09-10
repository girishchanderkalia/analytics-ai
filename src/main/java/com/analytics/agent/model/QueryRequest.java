package com.analytics.agent.model;

public record QueryRequest(String workspaceId, String table, String filter) {}
