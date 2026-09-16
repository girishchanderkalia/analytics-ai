package com.asml.analytics.facade.dto;

import java.util.Map;

/**
 * Response of GET /threads/{id}, per
 * contracts/workflow-runtime-api/openapi.yaml#/components/schemas/ThreadState.
 */
public class ThreadState {

    private String threadId;
    private String status;
    private Object request;
    private Map<String, Object> values;

    public String getThreadId() {
        return threadId;
    }

    public void setThreadId(String threadId) {
        this.threadId = threadId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Object getRequest() {
        return request;
    }

    public void setRequest(Object request) {
        this.request = request;
    }

    public Map<String, Object> getValues() {
        return values;
    }

    public void setValues(Map<String, Object> values) {
        this.values = values;
    }
}
