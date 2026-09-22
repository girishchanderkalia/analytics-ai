"""Create per-agent execution contexts from fixed framework components."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from bootstrap.capability_dispatcher_adapter import (
    CapabilityRegistryProtocol,
    create_capability_dispatcher,
)
from bootstrap.contract_provider import ContractProviderCache
from bootstrap.model_gateway_adapter import (
    PlatformModelGateway,
    create_model_gateway,
)
from bootstrap.operation_registry_bootstrap import (
    OperationHandler,
    create_operation_registry,
    validate_workflow_operations,
)
from execution.execution_context import ExecutionContext


class RuntimeContextFactoryError(RuntimeError):
    """Raised when an execution context cannot be created."""


@dataclass(frozen=True)
class ExecutionSecurityContext:
    """Authorization context applied to workflow capability calls."""

    permissions: frozenset[str] = field(default_factory=frozenset)
    approved_capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.permissions, frozenset):
            object.__setattr__(
                self,
                "permissions",
                frozenset(self.permissions),
            )
        if not isinstance(self.approved_capabilities, frozenset):
            object.__setattr__(
                self,
                "approved_capabilities",
                frozenset(self.approved_capabilities),
            )


class RuntimeContextFactory:
    """Create an ExecutionContext for one resolved agent bundle."""

    def __init__(
        self,
        capability_registry: CapabilityRegistryProtocol,
        operations: Mapping[str, OperationHandler],
        security_context: ExecutionSecurityContext | None = None,
        permissions: frozenset[str] | None = None,
        approved_capabilities: frozenset[str] | None = None,
        model_gateway: PlatformModelGateway | None = None,
        contract_provider_cache: ContractProviderCache | None = None,
    ) -> None:
        if not isinstance(operations, Mapping):
            raise RuntimeContextFactoryError(
                "operations must be a mapping"
            )

        if security_context is not None and (
            permissions is not None or approved_capabilities is not None
        ):
            raise RuntimeContextFactoryError(
                "Use security_context or explicit permission arguments, not both"
            )

        resolved_security = security_context or ExecutionSecurityContext(
            permissions=frozenset(permissions or ()),
            approved_capabilities=frozenset(
                approved_capabilities or ()
            ),
        )

        self.operations = dict(operations)
        self.permissions = resolved_security.permissions
        self.approved_capabilities = (
            resolved_security.approved_capabilities
        )
        self.model_gateway = (
            model_gateway
            if model_gateway is not None
            else create_model_gateway()
        )
        self.capability_dispatcher = create_capability_dispatcher(
            capability_registry
        )
        self.operation_registry = create_operation_registry(
            self.operations
        )
        self.contract_provider_cache = (
            contract_provider_cache
            if contract_provider_cache is not None
            else ContractProviderCache()
        )

    def create(self, bundle: Any) -> ExecutionContext:
        """Create an execution context for a resolved agent bundle."""

        if bundle is None:
            raise RuntimeContextFactoryError(
                "bundle must not be None"
            )

        validate_workflow_operations(bundle, self.operations)
        contract_provider = self.contract_provider_cache.get_or_create(
            bundle
        )

        return ExecutionContext(
            model_gateway=self.model_gateway,
            capability_dispatcher=self.capability_dispatcher,
            operation_registry=self.operation_registry,
            contract_provider=contract_provider,
            permissions=self.permissions,
            approved_capabilities=self.approved_capabilities,
        )

    def create_context(self, bundle: Any) -> ExecutionContext:
        """Compatibility alias for create()."""
        return self.create(bundle)

    def invalidate_contracts(
        self,
        agent_id: str | None = None,
        version: str | None = None,
    ) -> None:
        """Invalidate cached per-agent contracts."""
        self.contract_provider_cache.invalidate(
            agent_id=agent_id,
            version=version,
        )
