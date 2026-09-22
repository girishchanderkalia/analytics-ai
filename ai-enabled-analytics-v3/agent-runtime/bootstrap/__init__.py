"""Fixed framework bootstrap components."""

from .fixed_runtime_bootstrap import (
    create_application,
    create_execution_context,
)
from .model_gateway_adapter import (
    PlatformModelGateway,
    create_model_gateway,
)

__all__ = [
    "PlatformModelGateway",
    "create_application",
    "create_execution_context",
    "create_model_gateway",
]
