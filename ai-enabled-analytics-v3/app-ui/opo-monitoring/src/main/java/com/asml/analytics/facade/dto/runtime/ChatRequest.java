package com.asml.analytics.facade.dto.runtime;

import java.util.LinkedHashMap;
import java.util.Map;

public class ChatRequest {

    private String applicationId;
    private String agentId;
    private String version;
    private String conversationId;
    private Map<String, Object> initialState = new LinkedHashMap<>();

    public ChatRequest() {
    }

    public ChatRequest(
            String applicationId,
            String agentId,
            String version,
            String conversationId,
            Map<String, Object> initialState) {
        this.applicationId = applicationId;
        this.agentId = agentId;
        this.version = version;
        this.conversationId = conversationId;
        setInitialState(initialState);
    }

    public String getApplicationId() { return applicationId; }
    public void setApplicationId(String applicationId) { this.applicationId = applicationId; }
    public String getAgentId() { return agentId; }
    public void setAgentId(String agentId) { this.agentId = agentId; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public String getConversationId() { return conversationId; }
    public void setConversationId(String conversationId) { this.conversationId = conversationId; }
    public Map<String, Object> getInitialState() { return initialState; }
    public void setInitialState(Map<String, Object> initialState) {
        this.initialState = initialState == null
                ? new LinkedHashMap<>()
                : new LinkedHashMap<>(initialState);
    }
}
