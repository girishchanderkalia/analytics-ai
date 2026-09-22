"""Fixed framework bootstrap using the platform Model Gateway."""

from __future__ import annotations

from typing import Any

from execution.execution_context import ExecutionContext
from runtime_api import RuntimeSettings, create_production_app

from .model_gateway_adapter import create_model_gateway


def create_execution_context(
    capability_dispatcher: Any,
    operation_registry: Any,
    contract_provider: Any,
    permissions: frozenset[str] | None = None,
    approved_capabilities: frozenset[str] | None = None,
) -> ExecutionContext:
    """Compose the fixed execution dependencies.

    The Model Gateway is always created by the framework. The remaining fixed
    components are supplied by their existing framework bootstrap modules so
    this slice does not introduce duplicate registries or factories.
    """

    return ExecutionContext(
        model_gateway=create_model_gateway(),
        capability_dispatcher=capability_dispatcher,
        operation_registry=operation_registry,
        contract_provider=contract_provider,
        permissions=permissions or frozenset(),
        approved_capabilities=(
            approved_capabilities or frozenset()
        ),
    )


def create_application(
    capability_dispatcher: Any,
    operation_registry: Any,
    contract_provider: Any,
    permissions: frozenset[str] | None = None,
    approved_capabilities: frozenset[str] | None = None,
    settings: RuntimeSettings | None = None,
):
    """Create the persisted production API with the fixed Model Gateway."""

    context = create_execution_context(
        capability_dispatcher=capability_dispatcher,
        operation_registry=operation_registry,
        contract_provider=contract_provider,
        permissions=permissions,
        approved_capabilities=approved_capabilities,
    )

    return create_production_app(
        execution_context=context,
        settings=settings,
    )
