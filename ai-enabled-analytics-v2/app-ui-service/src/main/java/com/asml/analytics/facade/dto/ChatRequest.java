package com.asml.analytics.facade.dto;

/**
 * Request body for POST /chat, per
 * contracts/workflow-runtime-api/openapi.yaml#/components/schemas/ChatRequest.
 */
public class ChatRequest {

    private String message;
    private String threadId;

    public ChatRequest() {
    }

    public ChatRequest(String message, String threadId) {
        this.message = message;
        this.threadId = threadId;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getThreadId() {
        return threadId;
    }

    public void setThreadId(String threadId) {
        this.threadId = threadId;
    }
}
