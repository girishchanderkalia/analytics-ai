package com.asml.analytics.facade.dto.runtime;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class RuntimeResponse {

    private String applicationId;
    private String agentId;
    private String version;
    private String conversationId;
    private String status;
    private Map<String, Object> state = new LinkedHashMap<>();
    private List<RuntimeInterrupt> interrupts = new ArrayList<>();

    public String getApplicationId() { return applicationId; }
    public void setApplicationId(String applicationId) { this.applicationId = applicationId; }
    public String getAgentId() { return agentId; }
    public void setAgentId(String agentId) { this.agentId = agentId; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public String getConversationId() { return conversationId; }
    public void setConversationId(String conversationId) { this.conversationId = conversationId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Map<String, Object> getState() { return state; }
    public void setState(Map<String, Object> state) {
        this.state = state == null
                ? new LinkedHashMap<>()
                : new LinkedHashMap<>(state);
    }
    public List<RuntimeInterrupt> getInterrupts() { return interrupts; }
    public void setInterrupts(List<RuntimeInterrupt> interrupts) {
        this.interrupts = interrupts == null
                ? new ArrayList<>()
                : new ArrayList<>(interrupts);
    }

    public static class RuntimeInterrupt {
        private String interruptId;
        private Object value;

        public RuntimeInterrupt() {
        }

        public RuntimeInterrupt(String interruptId, Object value) {
            this.interruptId = interruptId;
            this.value = value;
        }

        public String getInterruptId() { return interruptId; }
        public void setInterruptId(String interruptId) { this.interruptId = interruptId; }
        public Object getValue() { return value; }
        public void setValue(Object value) { this.value = value; }
    }
}
