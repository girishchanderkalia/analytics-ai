package com.asml.analytics.facade.service;

import com.asml.analytics.facade.dto.RegistrationRequest;
import com.asml.analytics.facade.dto.RegistrationStatus;

/** Per .github/copilot-instructions.md `## 8`. */
public interface RegistrationService {
    RegistrationStatus register(RegistrationRequest request);
}
