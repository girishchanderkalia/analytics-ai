package com.asml.analytics.facade.client;
import com.asml.analytics.facade.dto.foundation.FoundationDtos.*;
import org.springframework.web.client.RestClient;

public final class HttpAnalyticsFoundationClient implements AnalyticsFoundationClient {
    private final RestClient client;
    public HttpAnalyticsFoundationClient(RestClient client) { this.client = client; }
    public TrendResponse queryTrends(TrendQuery r) { return call(() -> client.post().uri("/trends/query").body(r).retrieve().body(TrendResponse.class)); }
    public DistributionResponse getDistribution(DistributionQuery r) { return call(() -> client.post().uri("/trends/distribution").body(r).retrieve().body(DistributionResponse.class)); }
    public WorkspaceResponse createWorkspace(CreateWorkspaceRequest r) { return call(() -> client.post().uri("/workspaces").body(r).retrieve().body(WorkspaceResponse.class)); }
    public WorkspaceResponse applyFilters(String id, ApplyFiltersRequest r) { return call(() -> client.post().uri("/workspaces/{id}/filters",id).body(r).retrieve().body(WorkspaceResponse.class)); }
    public ConnectionInfoResponse getConnectionInfo(String id) { return call(() -> client.get().uri("/workspaces/{id}/connection-info",id).retrieve().body(ConnectionInfoResponse.class)); }
    public RegistrationResponse registerDataset(String id, RegistrationRequest r) { return call(() -> client.post().uri("/workspaces/{id}/registrations",id).body(r).retrieve().body(RegistrationResponse.class)); }
    public RegistrationResponse getRegistration(String w, String r) { return call(() -> client.get().uri("/workspaces/{w}/registrations/{r}",w,r).retrieve().body(RegistrationResponse.class)); }
    public WaferQueryResponse queryWafers(WaferQueryRequest r) { return call(() -> client.post().uri("/wafers/query").body(r).retrieve().body(WaferQueryResponse.class)); }
    private <T> T call(java.util.concurrent.Callable<T> action) { try { T value=action.call(); if(value==null) throw new IllegalStateException("Empty foundation response"); return value; } catch(Exception error) { throw new DownstreamClientException("analytics-foundation",error); } }
}
