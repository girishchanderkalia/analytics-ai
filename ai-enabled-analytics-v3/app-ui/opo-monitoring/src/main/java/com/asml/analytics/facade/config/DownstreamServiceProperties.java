package com.asml.analytics.facade.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "downstream-services")
public class DownstreamServiceProperties {

    private final Service runtime = new Service();
    private final Service analyticsFoundation = new Service();

    public Service getRuntime() {
        return runtime;
    }

    public Service getAnalyticsFoundation() {
        return analyticsFoundation;
    }

    // Accessors used by DownstreamClientConfiguration.
    public Service runtimeService() {
        return runtime;
    }

    public Service analyticsFoundation() {
        return analyticsFoundation;
    }

    public static class Service {
        private String baseUrl;
        private int connectTimeoutSeconds = 5;
        private int readTimeoutSeconds = 30;

        public String getBaseUrl() {
            return baseUrl;
        }

        // Record-style accessor used by DownstreamClientConfiguration.
        public String baseUrl() {
            return baseUrl;
        }

        public void setBaseUrl(String baseUrl) {
            this.baseUrl = normalizeBaseUrl(baseUrl);
        }

        public int getConnectTimeoutSeconds() {
            return connectTimeoutSeconds;
        }

        public int connectTimeoutSeconds() {
            return connectTimeoutSeconds;
        }

        public void setConnectTimeoutSeconds(int connectTimeoutSeconds) {
            this.connectTimeoutSeconds = requirePositive(
                    connectTimeoutSeconds,
                    "connectTimeoutSeconds");
        }

        public int getReadTimeoutSeconds() {
            return readTimeoutSeconds;
        }

        public int readTimeoutSeconds() {
            return readTimeoutSeconds;
        }

        public void setReadTimeoutSeconds(int readTimeoutSeconds) {
            this.readTimeoutSeconds = requirePositive(
                    readTimeoutSeconds,
                    "readTimeoutSeconds");
        }

        private static String normalizeBaseUrl(String value) {
            if (value == null || value.isBlank()) {
                return value;
            }
            String result = value.trim();
            while (result.endsWith("/")) {
                result = result.substring(0, result.length() - 1);
            }
            return result;
        }

        private static int requirePositive(int value, String field) {
            if (value <= 0) {
                throw new IllegalArgumentException(field + " must be positive");
            }
            return value;
        }
    }
}
