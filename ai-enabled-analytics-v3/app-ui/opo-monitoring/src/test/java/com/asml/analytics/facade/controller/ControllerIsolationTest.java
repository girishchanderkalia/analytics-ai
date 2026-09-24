package com.asml.analytics.facade.controller;
import static org.mockito.Mockito.*;
import com.asml.analytics.facade.client.*;
import com.asml.analytics.facade.dto.foundation.FoundationDtos.*;
import com.asml.analytics.facade.dto.runtime.*;
import java.util.*;
import org.junit.jupiter.api.Test;
class ControllerIsolationTest {
    @Test void investigationUsesRuntimeOnly(){
        RuntimeServiceClient runtime=mock(RuntimeServiceClient.class); ChatRequest request=new ChatRequest("a",null,"q",null,Map.of());
        new InvestigationController(runtime).chat(request); verify(runtime).chat(request);
    }
    @Test void trendUsesFoundationOnly(){
        AnalyticsFoundationClient foundation=mock(AnalyticsFoundationClient.class); TrendQuery request=new TrendQuery(Map.of(),List.of());
        new TrendController(foundation).query(request); verify(foundation).queryTrends(request);
    }
}
