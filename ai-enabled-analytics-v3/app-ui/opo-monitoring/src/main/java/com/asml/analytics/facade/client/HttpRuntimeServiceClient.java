package com.asml.analytics.facade.client;

import com.asml.analytics.facade.config.DownstreamServiceProperties;
import com.asml.analytics.facade.dto.runtime.ChatRequest;
import com.asml.analytics.facade.dto.runtime.ResumeRequest;
import com.asml.analytics.facade.dto.runtime.RuntimeResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

@Component
public final class HttpRuntimeServiceClient implements RuntimeServiceClient {
    private final JsonHttpSupport http;

    public HttpRuntimeServiceClient(
            @Qualifier("runtimeServiceHttpClient") HttpClient client,
            ObjectMapper mapper,
            DownstreamServiceProperties properties) {
        var service = properties.runtimeService();
        this.http = new JsonHttpSupport(
                client,
                mapper,
                service.baseUrl(),
                service.readTimeout());
    }

    @Override
    public RuntimeResponse start(ChatRequest request) {
        return http.post("/v1/chat", request, RuntimeResponse.class);
    }

    @Override
    public RuntimeResponse resume(
            String conversationId,
            ResumeRequest request) {
        return http.post(
                "/v1/conversations/" + segment(conversationId) + "/resume",
                request,
                RuntimeResponse.class);
    }

    @Override
    public RuntimeResponse getConversation(String conversationId) {
        return http.get(
                "/v1/conversations/" + segment(conversationId),
                RuntimeResponse.class);
    }

    private static String segment(String value) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("conversationId must not be blank");
        }
        return URLEncoder.encode(value, StandardCharsets.UTF_8)
                .replace("+", "%20");
    }
}
