package com.asml.analytics.facade;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * App/API facade entry point (PLAN.md Phase 5). Serves the app-facing HTTP
 * surface; all investigation/model/foundation access is delegated to the
 * Python workflow runtime via
 * {@link com.asml.analytics.facade.client.WorkflowRuntimeClient}.
 */
@SpringBootApplication
public class AnalyticsFacadeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AnalyticsFacadeApplication.class, args);
    }
}
