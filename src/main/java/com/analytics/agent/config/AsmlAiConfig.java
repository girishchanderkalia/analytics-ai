package com.analytics.agent.config;

import org.springframework.ai.model.NoopApiKey;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.openai.api.OpenAiApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

/**
 * Points the OpenAI client at the ASML gateway, which speaks the Azure OpenAI
 * dialect:
 * an {@code api-key} header and a
 * {@code /openai/deployments/{name}/chat/completions} path.
 */
@Configuration
public class AsmlAiConfig {

    @Bean
    OpenAiApi asmlOpenAiApi(@Value("${asml.ai.base-url}") String baseUrl,
            AsmlApiKeyProvider apiKeyProvider,
            @Value("${asml.ai.deployment}") String deployment,
            @Value("${asml.ai.api-version}") String apiVersion) {

        MultiValueMap<String, String> headers = new LinkedMultiValueMap<>();
        headers.add("api-key", apiKeyProvider.get());

        String completionsPath = "/openai/deployments/%s/chat/completions?api-version=%s"
                .formatted(deployment, apiVersion);

        return OpenAiApi.builder()
                .baseUrl(baseUrl)
                // NoopApiKey suppresses the Authorization header; the gateway authenticates on
                // api-key
                .apiKey(new NoopApiKey())
                .headers(headers)
                .completionsPath(completionsPath)
                .build();
    }

    @Bean
    OpenAiChatModel asmlChatModel(OpenAiApi asmlOpenAiApi,
            @Value("${asml.ai.deployment}") String deployment,
            @Value("${asml.ai.temperature}") Double temperature) {
        return OpenAiChatModel.builder()
                .openAiApi(asmlOpenAiApi)
                .defaultOptions(OpenAiChatOptions.builder()
                        .model(deployment)
                        .temperature(temperature)
                        .build())
                .build();
    }
}
