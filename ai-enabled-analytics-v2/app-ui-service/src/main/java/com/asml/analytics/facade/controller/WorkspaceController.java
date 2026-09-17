package com.asml.analytics.facade.controller;

import com.asml.analytics.facade.dto.Filters;
import com.asml.analytics.facade.dto.QueryRequest;
import com.asml.analytics.facade.dto.RegistrationRequest;
import com.asml.analytics.facade.dto.RegistrationStatus;
import com.asml.analytics.facade.dto.WaferResult;
import com.asml.analytics.facade.service.RegistrationService;
import com.asml.analytics.facade.service.WaferDataService;
import com.asml.analytics.facade.service.WorkspaceService;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Collections;
import java.util.Map;

/**
 * Traditional (non-agentic) deep-dive routes for the app's manual investigation
 * path. Each call still reaches Foundation data only through the Python
 * workflow runtime's API (never MCP/foundation directly from Java).
 */
@RestController
@RequestMapping("/workspaces")
public class WorkspaceController {

    private final WorkspaceService workspaceService;
    private final RegistrationService registrationService;
    private final WaferDataService waferDataService;

    public WorkspaceController(
            WorkspaceService workspaceService,
            RegistrationService registrationService,
            WaferDataService waferDataService) {
        this.workspaceService = workspaceService;
        this.registrationService = registrationService;
        this.waferDataService = waferDataService;
    }

    @PostMapping
    public Map<String, String> createWorkspace() {
        return Collections.singletonMap("workspace_id", workspaceService.createWorkspace());
    }

    @PostMapping("/{workspaceId}/filters")
    public void addFilters(@PathVariable String workspaceId, @RequestBody Map<String, Object> filters) {
        Filters value = new Filters();
        filters.forEach(value::put);
        workspaceService.addFilters(workspaceId, value);
    }

    @PostMapping("/{workspaceId}/register")
    public RegistrationStatus register(@PathVariable String workspaceId, @RequestBody RegistrationRequest request) {
        request.setWorkspaceId(workspaceId);
        return registrationService.register(request);
    }

    @PostMapping("/{workspaceId}/wafers/query")
    public WaferResult queryWafers(@PathVariable String workspaceId, @RequestBody QueryRequest request) {
        request.setWorkspaceId(workspaceId);
        return waferDataService.query(request);
    }
}
