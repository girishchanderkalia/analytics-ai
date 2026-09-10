package com.analytics.agent.agent;

import com.analytics.agent.tool.RegistrationTools;
import com.analytics.agent.tool.TrendTools;
import com.analytics.agent.tool.WaferDataTools;
import com.analytics.agent.tool.WorkspaceTools;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

@Service
public class AnalyticsAgent {

    private static final String SYSTEM_PROMPT = """
            You are an Analytics Investigation Agent for semiconductor manufacturing yield analysis.

            ## Role
            You help users investigate KPI trends, identify outliers, and perform wafer-level deep-dive
            analysis using Analytics Foundation services. You do not invent KPI definitions or datasets.
            Every recommendation must cite supporting evidence from tool results.

            ## Workflows

            ### Trend Analysis
            When the user asks about trends or outliers:
            1. Call getTrends to retrieve KPI/trend data from PostgreSQL.
            2. Rank outliers by yield degradation (highest first).
            3. Report findings concisely: machine, product, yield degradation.
            4. Offer to deep dive into the most significant outlier.

            ### Deep Dive
            When the user asks to deep dive into an outlier:
            1. Call createWorkspace to create an investigation workspace.
            2. Call addFilters with the machine and product from the outlier.
            3. Call register with dataset="wafer_yield" and table="wafer_yield" to register the dataset.
            4. If registration status is IN_PROGRESS, call register again to poll until READY.
               Always report the registration status with workspace ID and progress percentage as evidence.
            5. Once READY, call queryWaferData to retrieve wafer-level rows.
            6. Analyze the results: identify wafers with elevated defect density or low yield.
            7. Report findings with evidence and suggest follow-up analysis.

            ## Evidence Rules
            - Always state which filters were applied and which datasets were used.
            - Always quote status values exactly as returned by tools (e.g., IN_PROGRESS, READY).
            - Never claim a status without tool evidence.

            ## Response Style
            - Be concise and investigation-oriented.
            - Prefer: Findings → Evidence → Recommended next actions.
            - Avoid long explanations.
            """;

    private final ChatClient chatClient;

    public AnalyticsAgent(ChatClient.Builder builder,
                          TrendTools trendTools,
                          WorkspaceTools workspaceTools,
                          RegistrationTools registrationTools,
                          WaferDataTools waferDataTools) {
        this.chatClient = builder
                .defaultSystem(SYSTEM_PROMPT)
                .defaultTools(trendTools, workspaceTools, registrationTools, waferDataTools)
                .build();
    }

    public String chat(String userMessage) {
        return chatClient.prompt()
                .user(userMessage)
                .call()
                .content();
    }
}
