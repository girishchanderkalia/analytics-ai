package com.asml.analytics.facade.controller;
import com.asml.analytics.facade.client.RuntimeServiceClient;
import com.asml.analytics.facade.dto.runtime.*;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/investigations")
public class InvestigationController {
    private final RuntimeServiceClient client;
    public InvestigationController(RuntimeServiceClient client) { this.client=client; }
    @PostMapping("/chat") public RuntimeResponse chat(@Valid @RequestBody ChatRequest request) { return client.chat(request); }
    @PostMapping("/{id}/resume") public RuntimeResponse resume(@PathVariable String id,@RequestBody ResumeRequest request) { return client.resume(id,request); }
    @GetMapping("/{id}") public RuntimeResponse get(@PathVariable String id) { return client.getConversation(id); }
}
