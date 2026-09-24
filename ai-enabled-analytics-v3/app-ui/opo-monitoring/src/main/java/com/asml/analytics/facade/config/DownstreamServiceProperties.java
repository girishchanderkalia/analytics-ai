package com.asml.analytics.facade.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "downstream")
public record DownstreamServiceProperties(
        Service runtimeService,
        Service analyticsFoundation) {

    public DownstreamServiceProperties {
        runtimeService = requireService(runtimeService, "runtime-service");
        analyticsFoundation = requireService(
                analyticsFoundation,
                "analytics-foundation");
    }

    private static Service requireService(Service service, String name) {
        if (service == null) {
            throw new IllegalArgumentException(
                    "downstream." + name + " configuration is required");
        }
        return service;
    }

    public record Service(
            String baseUrl,
            Duration connectTimeout,
            Duration readTimeout) {

        public Service {
            if (baseUrl == null || baseUrl.isBlank()) {
                throw new IllegalArgumentException("baseUrl must not be blank");
            }
            baseUrl = baseUrl.replaceAll("/+$", "");
            connectTimeout = positive(connectTimeout, "connectTimeout");
            readTimeout = positive(readTimeout, "readTimeout");
        }

        private static Duration positive(Duration value, String field) {
            if (value == null || value.isZero() || value.isNegative()) {
                throw new IllegalArgumentException(field + " must be positive");
            }
            return value;
        }
    }
}
