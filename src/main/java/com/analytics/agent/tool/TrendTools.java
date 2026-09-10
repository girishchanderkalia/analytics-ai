package com.analytics.agent.tool;

import com.analytics.agent.model.TrendResponse;
import com.analytics.agent.service.TrendService;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.stereotype.Component;

@Component
public class TrendTools {

    private final TrendService trendService;

    public TrendTools(TrendService trendService) {
        this.trendService = trendService;
    }

    @Tool(description = """
            Query PostgreSQL KPI/trend data and return all detected outliers.
            Each outlier includes the machine name, product, and yield degradation percentage.
            Use this to answer questions about trends, anomalies, or outliers.
            """)
    public TrendResponse getTrends() {
        return trendService.getTrends();
    }
}
