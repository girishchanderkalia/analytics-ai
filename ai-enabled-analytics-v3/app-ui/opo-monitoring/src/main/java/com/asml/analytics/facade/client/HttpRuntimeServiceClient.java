package com.asml.analytics.facade.client;
import com.asml.analytics.facade.dto.runtime.ChatRequest;
import com.asml.analytics.facade.dto.runtime.ResumeRequest;
import com.asml.analytics.facade.dto.runtime.RuntimeResponse;
import org.springframework.web.client.RestClient;

public final class HttpRuntimeServiceClient implements RuntimeServiceClient {
    private final RestClient client;
    public HttpRuntimeServiceClient(RestClient client) { this.client = client; }
    public RuntimeResponse chat(ChatRequest request) { return execute(() -> client.post().uri("/v1/chat").body(request).retrieve().body(RuntimeResponse.class)); }
    public RuntimeResponse resume(String id, ResumeRequest request) { return execute(() -> client.post().uri("/v1/conversations/{id}/resume", id).body(request).retrieve().body(RuntimeResponse.class)); }
    public RuntimeResponse getConversation(String id) { return execute(() -> client.get().uri("/v1/conversations/{id}", id).retrieve().body(RuntimeResponse.class)); }
    private RuntimeResponse execute(java.util.concurrent.Callable<RuntimeResponse> action) {
        try { RuntimeResponse value = action.call(); if (value == null) throw new IllegalStateException("Empty runtime response"); return value; }
        catch (Exception error) { throw new DownstreamClientException("runtime-service", error); }
    }
}
