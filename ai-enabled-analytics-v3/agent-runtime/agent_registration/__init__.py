"""Bulk registration of prebuilt application agents."""

from .catalog import InMemoryAgentRegistrationCatalog
from .errors import (
    AgentAlreadyRegisteredError,
    AgentRegistrationError,
    AgentRegistrationValidationError,
)
from .models import (
    AgentRegistrationKey,
    AgentRegistrationRecord,
    AgentRegistrationRequest,
    BulkAgentRegistrationRequest,
    BulkAgentRegistrationResult,
    RegistrationStatus,
)
from .service import AgentRegistrationService, AgentRegistrationValidator

__all__ = [
    "AgentAlreadyRegisteredError",
    "AgentRegistrationError",
    "AgentRegistrationKey",
    "AgentRegistrationRecord",
    "AgentRegistrationRequest",
    "AgentRegistrationService",
    "AgentRegistrationValidationError",
    "AgentRegistrationValidator",
    "BulkAgentRegistrationRequest",
    "BulkAgentRegistrationResult",
    "InMemoryAgentRegistrationCatalog",
    "RegistrationStatus",
]
