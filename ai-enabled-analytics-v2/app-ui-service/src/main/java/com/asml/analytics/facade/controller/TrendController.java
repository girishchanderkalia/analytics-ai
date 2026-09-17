package com.asml.analytics.facade.controller;

import com.asml.analytics.facade.dto.TrendResponse;
import com.asml.analytics.facade.service.TrendService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Traditional (non-agentic) display route: GET /trends, no agent or MCP
 * involved.
 */
@RestController
public class TrendController {

    private final TrendService trendService;

    public TrendController(TrendService trendService) {
        this.trendService = trendService;
    }

    @GetMapping("/trends")
    public TrendResponse getTrends() {
        return trendService.getTrends();
    }
}
