package com.asml.analytics.facade.dto;

import java.util.Map;

/**
 * Response of POST /chat and POST /resume, per
 * contracts/workflow-runtime-api/openapi.yaml#/components/schemas/InvestigationResponse.
 * `findings` mirrors contracts/model/FindingsSummary.schema.json but is kept as
 * a Map here since the facade only ever passes it through to the app, never
 * interprets it (that stays application/model-owned per the language boundary).
 */
public class InvestigationResponse {

    private String threadId;
    private String status;
    private Object request;
    private String cancelledAt;
    private Map<String, Object> findings;
    private Map<String, Object> evidence;

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

    public String getCancelledAt() {
        return cancelledAt;
    }

    public void setCancelledAt(String cancelledAt) {
        this.cancelledAt = cancelledAt;
    }

    public Map<String, Object> getFindings() {
        return findings;
    }

    public void setFindings(Map<String, Object> findings) {
        this.findings = findings;
    }

    public Map<String, Object> getEvidence() {
        return evidence;
    }

    public void setEvidence(Map<String, Object> evidence) {
        this.evidence = evidence;
    }
}
