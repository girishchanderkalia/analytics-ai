package com.asml.analytics.facade.controller;
import com.asml.analytics.facade.client.AnalyticsFoundationClient;
import com.asml.analytics.facade.dto.foundation.FoundationDtos.*;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/workspaces")
public class WorkspaceController {
    private final AnalyticsFoundationClient client;
    public WorkspaceController(AnalyticsFoundationClient client){this.client=client;}
    @PostMapping public WorkspaceResponse create(@RequestBody CreateWorkspaceRequest r){return client.createWorkspace(r);}
    @PostMapping("/{id}/filters") public WorkspaceResponse filters(@PathVariable String id,@RequestBody ApplyFiltersRequest r){return client.applyFilters(id,r);}
    @GetMapping("/{id}/connection-info") public ConnectionInfoResponse connection(@PathVariable String id){return client.getConnectionInfo(id);}
    @PostMapping("/{id}/registrations") public RegistrationResponse register(@PathVariable String id,@RequestBody RegistrationRequest r){return client.registerDataset(id,r);}
    @GetMapping("/{w}/registrations/{r}") public RegistrationResponse registration(@PathVariable String w,@PathVariable String r){return client.getRegistration(w,r);}
}
