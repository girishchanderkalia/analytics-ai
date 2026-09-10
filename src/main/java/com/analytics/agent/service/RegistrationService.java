package com.analytics.agent.service;

import com.analytics.agent.model.RegistrationRequest;
import com.analytics.agent.model.RegistrationStatus;

public interface RegistrationService {
    RegistrationStatus register(RegistrationRequest request);
}
