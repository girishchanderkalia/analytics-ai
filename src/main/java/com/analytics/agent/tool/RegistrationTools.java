package com.analytics.agent.tool;

import com.analytics.agent.model.RegistrationRequest;
import com.analytics.agent.model.RegistrationStatus;
import com.analytics.agent.service.RegistrationService;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class RegistrationTools {

    private final RegistrationService registrationService;

    public RegistrationTools(RegistrationService registrationService) {
        this.registrationService = registrationService;
    }

    @Tool(description = """
            Register a dataset/table into a workspace via Analytics Foundation.
            Returns the registration status (IN_PROGRESS or READY) with progress percentage.
            If status is IN_PROGRESS, call this tool again with the same request to poll for readiness.
            Only proceed to query wafer data once status is READY.
            """)
    public RegistrationStatus register(
            @ToolParam(description = "Registration request with workspaceId, dataset name, and table name") RegistrationRequest request) {
        return registrationService.register(request);
    }
}
