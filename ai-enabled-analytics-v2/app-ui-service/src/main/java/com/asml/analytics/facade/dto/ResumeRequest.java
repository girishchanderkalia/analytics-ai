package com.asml.analytics.facade.dto;

/**
 * Request body for POST /resume. `decision` may be a boolean or an object; kept
 * as Object.
 */
public class ResumeRequest {

    private String threadId;
    private Object decision;

    public ResumeRequest() {
    }

    public ResumeRequest(String threadId, Object decision) {
        this.threadId = threadId;
        this.decision = decision;
    }

    public String getThreadId() {
        return threadId;
    }

    public void setThreadId(String threadId) {
        this.threadId = threadId;
    }

    public Object getDecision() {
        return decision;
    }

    public void setDecision(Object decision) {
        this.decision = decision;
    }
}
