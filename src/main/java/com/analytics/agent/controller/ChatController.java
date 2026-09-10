package com.analytics.agent.controller;

import com.analytics.agent.agent.AnalyticsAgent;
import com.analytics.agent.model.ChatRequest;
import com.analytics.agent.model.ChatResponse;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChatController {

    private final AnalyticsAgent analyticsAgent;

    public ChatController(AnalyticsAgent analyticsAgent) {
        this.analyticsAgent = analyticsAgent;
    }

    @PostMapping("/chat")
    public ChatResponse chat(@RequestBody ChatRequest request) {
        String reply = analyticsAgent.chat(request.message());
        return new ChatResponse(reply);
    }
}
