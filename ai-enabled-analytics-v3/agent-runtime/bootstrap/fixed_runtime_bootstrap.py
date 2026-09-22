"""Fixed framework bootstrap for model and capability execution."""

from __future__ import annotations

from typing import Any

from execution.execution_context import ExecutionContext
from runtime_api import RuntimeSettings, create_production_app

from .capability_dispatcher_adapter import (
    CapabilityRegistryProtocol,
    create_capability_dispatcher,
)
from .model_gateway_adapter import create_model_gateway


def create_execution_context(
    capability_registry: CapabilityRegistryProtocol,
    operation_registry: Any,
    contract_provider: Any,
    permissions: frozenset[str] | None = None,
    approved_capabilities: frozenset[str] | None = None,
) -> ExecutionContext:
    """Compose fixed model and capability infrastructure."""

    return ExecutionContext(
        model_gateway=create_model_gateway(),
        capability_dispatcher=create_capability_dispatcher(
            capability_registry
        ),
        operation_registry=operation_registry,
        contract_provider=contract_provider,
        permissions=permissions or frozenset(),
        approved_capabilities=(
            approved_capabilities or frozenset()
        ),
    )


def create_application(
    capability_registry: CapabilityRegistryProtocol,
    operation_registry: Any,
    contract_provider: Any,
    permissions: frozenset[str] | None = None,
    approved_capabilities: frozenset[str] | None = None,
    settings: RuntimeSettings | None = None,
):
    """Create the persisted production API from fixed runtime components."""

    context = create_execution_context(
        capability_registry=capability_registry,
        operation_registry=operation_registry,
        contract_provider=contract_provider,
        permissions=permissions,
        approved_capabilities=approved_capabilities,
    )

    return create_production_app(
        execution_context=context,
        settings=settings,
    )
