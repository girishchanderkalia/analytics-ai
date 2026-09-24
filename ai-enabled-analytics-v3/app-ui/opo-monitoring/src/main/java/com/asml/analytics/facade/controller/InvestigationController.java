package com.asml.analytics.facade.controller;

import com.asml.analytics.facade.client.RuntimeServiceClient;
import com.asml.analytics.facade.dto.runtime.ChatRequest;
import com.asml.analytics.facade.dto.runtime.ResumeRequest;
import com.asml.analytics.facade.dto.runtime.RuntimeResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/investigations")
public final class InvestigationController {
    private final RuntimeServiceClient runtimeService;

    public InvestigationController(RuntimeServiceClient runtimeService) {
        this.runtimeService = runtimeService;
    }

    @PostMapping("/chat")
    public RuntimeResponse start(@RequestBody ChatRequest request) {
        return runtimeService.start(request);
    }

    @PostMapping("/{conversationId}/resume")
    public RuntimeResponse resume(
            @PathVariable String conversationId,
            @RequestBody ResumeRequest request) {
        return runtimeService.resume(conversationId, request);
    }

    @GetMapping("/{conversationId}")
    public RuntimeResponse get(@PathVariable String conversationId) {
        return runtimeService.getConversation(conversationId);
    }
}
