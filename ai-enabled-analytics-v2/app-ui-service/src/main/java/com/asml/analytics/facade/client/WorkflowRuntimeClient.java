package com.asml.analytics.facade.client;

import com.asml.analytics.facade.config.WorkflowRuntimeProperties;
import com.asml.analytics.facade.dto.ChatRequest;
import com.asml.analytics.facade.dto.InvestigationResponse;
import com.asml.analytics.facade.dto.RegistrationStatus;
import com.asml.analytics.facade.dto.ResumeRequest;
import com.asml.analytics.facade.dto.ThreadState;
import com.asml.analytics.facade.dto.TrendResponse;
import com.asml.analytics.facade.dto.WaferResult;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.Map;

/**
 * The ONE HTTP client to the Python workflow runtime
 * (contracts/workflow-runtime-api/openapi.yaml). Per the language boundary
 * (.github/copilot-instructions.md `### 2.1`), nothing else in app-ui-service
 * may open a socket to Foundation APIs, MCP, or the model gateway; every
 * service implementation goes through this class.
 */
@Component
public class WorkflowRuntimeClient {

    private final RestTemplate restTemplate;
    private final WorkflowRuntimeProperties properties;

    public WorkflowRuntimeClient(RestTemplate restTemplate, WorkflowRuntimeProperties properties) {
        this.restTemplate = restTemplate;
        this.properties = properties;
    }

    private String url(String path) {
        return properties.getBaseUrl() + path;
    }

    public TrendResponse getTrends() {
        return restTemplate.getForObject(url("/trends"), TrendResponse.class);
    }

    public InvestigationResponse chat(ChatRequest request) {
        return restTemplate.postForObject(url("/chat"), request, InvestigationResponse.class);
    }

    public InvestigationResponse resume(ResumeRequest request) {
        return restTemplate.postForObject(url("/resume"), request, InvestigationResponse.class);
    }

    public ThreadState getThreadState(String threadId) {
        return restTemplate.getForObject(url("/threads/" + threadId), ThreadState.class);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getSessionEvents(String sessionId) {
        return restTemplate.getForObject(url("/sessions/" + sessionId + "/events"), Map.class);
    }

    public String createWorkspace() {
        Map<String, Object> response = restTemplate.postForObject(url("/workspaces"), null, Map.class);
        return response == null ? null : String.valueOf(response.get("workspace_id"));
    }

    public void addFilters(String workspaceId, Map<String, Object> filters) {
        restTemplate.postForObject(
                url("/workspaces/" + workspaceId + "/filters"),
                Collections.singletonMap("filters", filters),
                Map.class);
    }

    public RegistrationStatus register(String workspaceId, String dataset, String table) {
        Map<String, Object> body = new java.util.HashMap<>();
        body.put("dataset", dataset);
        body.put("table", table);
        return restTemplate.postForObject(
                url("/workspaces/" + workspaceId + "/register"), body, RegistrationStatus.class);
    }

    public WaferResult queryWafers(String workspaceId, String table, Map<String, Object> filters) {
        Map<String, Object> body = new java.util.HashMap<>();
        body.put("table", table);
        body.put("filters", filters);
        return restTemplate.postForObject(
                url("/workspaces/" + workspaceId + "/wafers/query"), body, WaferResult.class);
    }
}
