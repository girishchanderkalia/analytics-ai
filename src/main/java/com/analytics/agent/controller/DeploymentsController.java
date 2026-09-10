package com.analytics.agent.controller;

import com.analytics.agent.config.AsmlApiKeyProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

/**
 * Lists gateway deployments so the correct value for asml.ai.deployment can be
 * discovered.
 */
@RestController
public class DeploymentsController {

    private final RestClient restClient;
    private final String apiKey;

    public DeploymentsController(@Value("${asml.ai.base-url}") String baseUrl,
            AsmlApiKeyProvider apiKeyProvider) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.apiKey = apiKeyProvider.get();
    }

    @GetMapping("/deployments")
    public List<String> deployments() {
        @SuppressWarnings("unchecked")
        Map<String, Object> body = restClient.get()
                .uri("/openai/deployments")
                .header("api-key", apiKey)
                .retrieve()
                .body(Map.class);

        if (body == null) {
            return List.of();
        }
        List<?> data = (List<?>) body.getOrDefault("data", List.of());
        return data.stream()
                .map(item -> String.valueOf(((Map<?, ?>) item).get("model")))
                .toList();
    }
}
