package com.asml.analytics.facade.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** Binds the `workflow-runtime.*` settings in application.yml. */
@Component
@ConfigurationProperties(prefix = "workflow-runtime")
public class WorkflowRuntimeProperties {

    private String baseUrl;

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}
