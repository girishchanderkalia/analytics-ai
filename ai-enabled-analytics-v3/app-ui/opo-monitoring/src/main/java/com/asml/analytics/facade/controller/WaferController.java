package com.asml.analytics.facade.controller;
import com.asml.analytics.facade.client.AnalyticsFoundationClient;
import com.asml.analytics.facade.dto.foundation.WaferQueryRequest;
import com.asml.analytics.facade.dto.foundation.WaferQueryResponse;
import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/api/wafers")
public class WaferController {
    private final AnalyticsFoundationClient client;
    public WaferController(AnalyticsFoundationClient client){this.client=client;}
    @PostMapping("/query") public WaferQueryResponse query(@RequestBody WaferQueryRequest r){return client.queryWafers(r);}
}
