package com.asml.analytics.facade.controller;

import com.asml.analytics.facade.client.WorkflowRuntimeClient;
import com.asml.analytics.facade.dto.ChatRequest;
import com.asml.analytics.facade.dto.InvestigationResponse;
import com.asml.analytics.facade.dto.ResumeRequest;
import com.asml.analytics.facade.dto.ThreadState;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * Conversational investigation routes. The facade does not interpret intent or
 * evidence itself (that stays Python/agent-owned per the language boundary); it
 * only forwards to the workflow runtime and returns its response as-is.
 */
@RestController
public class InvestigationController {

    private final WorkflowRuntimeClient client;

    public InvestigationController(WorkflowRuntimeClient client) {
        this.client = client;
    }

    @PostMapping("/chat")
    public InvestigationResponse chat(@RequestBody ChatRequest request) {
        return client.chat(request);
    }

    @PostMapping("/resume")
    public InvestigationResponse resume(@RequestBody ResumeRequest request) {
        return client.resume(request);
    }

    @GetMapping("/threads/{threadId}")
    public ThreadState threadState(@PathVariable String threadId) {
        return client.getThreadState(threadId);
    }
}
