package com.asml.analytics.facade.client;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;

class ClientRouteContractTest {
    @Test
    void clientsUseSeparatedDownstreamRoutes() throws Exception {
        String runtime = Files.readString(Path.of(
                "src/main/java/com/asml/analytics/facade/client/HttpRuntimeServiceClient.java"));
        String foundation = Files.readString(Path.of(
                "src/main/java/com/asml/analytics/facade/client/HttpAnalyticsFoundationClient.java"));

        assertTrue(runtime.contains("/v1/chat"));
        assertTrue(runtime.contains("/v1/conversations/"));
        assertTrue(!runtime.contains("/trends/query"));
        assertTrue(foundation.contains("/trends/query"));
        assertTrue(foundation.contains("/workspaces"));
        assertTrue(foundation.contains("/wafers/query"));
        assertTrue(!foundation.contains("/v1/chat"));
    }
}
