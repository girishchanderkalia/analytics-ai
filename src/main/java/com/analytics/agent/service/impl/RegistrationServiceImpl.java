package com.analytics.agent.service.impl;

import com.analytics.agent.model.RegistrationRequest;
import com.analytics.agent.model.RegistrationStatus;
import com.analytics.agent.service.RegistrationService;
import org.springframework.stereotype.Service;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Service
public class RegistrationServiceImpl implements RegistrationService {

    // tracks call count per workspaceId to simulate progress
    private final ConcurrentHashMap<String, AtomicInteger> callCounts = new ConcurrentHashMap<>();

    @Override
    public RegistrationStatus register(RegistrationRequest request) {
        AtomicInteger count = callCounts.computeIfAbsent(request.workspaceId(), k -> new AtomicInteger(0));
        int calls = count.incrementAndGet();

        if (calls < 3) {
            int progress = calls * 33;
            return new RegistrationStatus("IN_PROGRESS", request.workspaceId(), progress, request.table());
        }
        return new RegistrationStatus("READY", request.workspaceId(), 100, request.table());
    }
}
