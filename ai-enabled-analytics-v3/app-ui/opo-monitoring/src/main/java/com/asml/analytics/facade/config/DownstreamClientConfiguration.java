package com.asml.analytics.facade.config;

import com.asml.analytics.facade.client.AnalyticsFoundationClient;
import com.asml.analytics.facade.client.HttpAnalyticsFoundationClient;
import com.asml.analytics.facade.client.HttpRuntimeServiceClient;
import com.asml.analytics.facade.client.RuntimeServiceClient;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(DownstreamServiceProperties.class)
public class DownstreamClientConfiguration {
    @Bean
    RuntimeServiceClient runtimeServiceClient(RestClient.Builder builder, DownstreamServiceProperties properties) {
        return new HttpRuntimeServiceClient(builder.baseUrl(properties.runtimeService().baseUrl()).build());
    }

    @Bean
    AnalyticsFoundationClient analyticsFoundationClient(RestClient.Builder builder, DownstreamServiceProperties properties) {
        return new HttpAnalyticsFoundationClient(builder.baseUrl(properties.analyticsFoundation().baseUrl()).build());
    }
}
