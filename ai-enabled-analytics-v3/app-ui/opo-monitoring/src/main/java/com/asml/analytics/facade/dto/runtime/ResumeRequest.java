package com.asml.analytics.facade.dto.runtime;

public class ResumeRequest {

    private String applicationId;
    private String agentId;
    private String version;
    private String conversationId;
    private Object resumeValue;
    private String interruptId;

    public ResumeRequest() {
    }

    public ResumeRequest(
            String applicationId,
            String agentId,
            String version,
            String conversationId,
            Object resumeValue,
            String interruptId) {
        this.applicationId = applicationId;
        this.agentId = agentId;
        this.version = version;
        this.conversationId = conversationId;
        this.resumeValue = resumeValue;
        this.interruptId = interruptId;
    }

    public String getApplicationId() { return applicationId; }
    public void setApplicationId(String applicationId) { this.applicationId = applicationId; }
    public String getAgentId() { return agentId; }
    public void setAgentId(String agentId) { this.agentId = agentId; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public String getConversationId() { return conversationId; }
    public void setConversationId(String conversationId) { this.conversationId = conversationId; }
    public Object getResumeValue() { return resumeValue; }
    public void setResumeValue(Object resumeValue) { this.resumeValue = resumeValue; }
    public String getInterruptId() { return interruptId; }
    public void setInterruptId(String interruptId) { this.interruptId = interruptId; }
}
