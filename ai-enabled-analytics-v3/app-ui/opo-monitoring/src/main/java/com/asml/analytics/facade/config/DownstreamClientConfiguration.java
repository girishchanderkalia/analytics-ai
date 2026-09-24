package com.asml.analytics.facade.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.http.HttpClient;
import java.time.Duration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(DownstreamServiceProperties.class)
public class DownstreamClientConfiguration {

    @Bean("runtimeServiceHttpClient")
    HttpClient runtimeServiceHttpClient(
            DownstreamServiceProperties properties) {
        return client(properties.runtimeService().connectTimeout());
    }

    @Bean("analyticsFoundationHttpClient")
    HttpClient analyticsFoundationHttpClient(
            DownstreamServiceProperties properties) {
        return client(properties.analyticsFoundation().connectTimeout());
    }

    @Bean
    ObjectMapper downstreamObjectMapper() {
        return new ObjectMapper().findAndRegisterModules();
    }

    private static HttpClient client(Duration connectTimeout) {
        return HttpClient.newBuilder()
                .connectTimeout(connectTimeout)
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();
    }
}
