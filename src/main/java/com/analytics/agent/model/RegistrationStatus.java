package com.analytics.agent.model;

public record RegistrationStatus(String status, String workspaceId, int progressPct, String requiredTable) {}
