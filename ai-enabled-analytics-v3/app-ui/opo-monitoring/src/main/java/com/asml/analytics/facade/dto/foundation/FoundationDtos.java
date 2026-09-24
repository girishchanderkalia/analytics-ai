package com.asml.analytics.facade.dto.foundation;

import java.util.List;
import java.util.Map;

public final class FoundationDtos {
    private FoundationDtos() {}
    public record TrendQuery(Map<String,Object> filters, List<String> groupBy) {}
    public record TrendResponse(List<Map<String,Object>> series, Map<String,Object> metadata) {}
    public record DistributionQuery(Map<String,Object> filters, String metric) {}
    public record DistributionResponse(long count, Double minimum, Double maximum, Double mean, Map<String,Object> quantiles) {}
    public record CreateWorkspaceRequest(String name, Map<String,Object> context) {}
    public record WorkspaceResponse(String workspaceId, String status, Map<String,Object> details) {}
    public record ApplyFiltersRequest(Map<String,Object> filters) {}
    public record ConnectionInfoResponse(String workspaceId, Map<String,Object> connectionInfo) {}
    public record RegistrationRequest(String datasetName, Map<String,Object> options) {}
    public record RegistrationResponse(String registrationId, String workspaceId, String status, Map<String,Object> details) {}
    public record WaferQueryRequest(Map<String,Object> filters, List<String> fields) {}
    public record WaferQueryResponse(List<Map<String,Object>> rows, Map<String,Object> metadata) {}
}
