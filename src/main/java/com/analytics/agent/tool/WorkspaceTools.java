package com.analytics.agent.tool;

import com.analytics.agent.model.Filters;
import com.analytics.agent.service.WorkspaceService;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class WorkspaceTools {

    private final WorkspaceService workspaceService;

    public WorkspaceTools(WorkspaceService workspaceService) {
        this.workspaceService = workspaceService;
    }

    @Tool(description = """
            Create a new investigation workspace via Analytics Foundation.
            Returns the workspace ID to use in subsequent operations.
            Always call this before registering datasets or querying wafer data.
            """)
    public String createWorkspace() {
        return workspaceService.createWorkspace();
    }

    @Tool(description = """
            Apply investigation filters to an existing workspace.
            Filters narrow the scope to a specific machine, product, and time range.
            Must be called after createWorkspace and before registering datasets.
            """)
    public void addFilters(
            @ToolParam(description = "The workspace ID returned by createWorkspace") String workspaceId,
            @ToolParam(description = "Filters to apply: machine, product, and time range") Filters filters) {
        workspaceService.addFilters(workspaceId, filters);
    }
}
