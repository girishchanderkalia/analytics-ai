"""Compose validated agent bundles into executable runtimes."""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any

from catalog.catalog_models import AgentCatalogEntry
from execution.contract_factory import ContractFactory
from execution.execution_context import ExecutionContext
from execution.operation_registry import OperationRegistry
from execution.workflow_engine import WorkflowEngine


class RuntimeCompositionError(ValueError):
    """Raised when an executable agent runtime cannot be composed."""


class ContractProviderAdapter:
    """Expose ContractFactory through the NodeExecutor contract-provider API."""

    def __init__(self, factory: ContractFactory) -> None:
        self.factory = factory

    def get_contract(self, contract_name: str) -> type[Any]:
        return self.factory.get(contract_name)


@dataclass(frozen=True)
class ComposedAgentRuntime:
    """All runtime objects assembled for one agent version."""

    entry: AgentCatalogEntry
    contract_provider: Any
    operation_registry: Any
    capability_dispatcher: Any
    execution_context: ExecutionContext
    workflow_engine: WorkflowEngine


RuntimeFactory = Callable[[AgentCatalogEntry], Any]
PermissionsProvider = Callable[[AgentCatalogEntry], Collection[str]]


class RuntimeComposer:
    """Build a WorkflowEngine and its dependencies for one catalog entry."""

    def __init__(
        self,
        model_gateway_factory: RuntimeFactory,
        capability_dispatcher_factory: RuntimeFactory,
        operation_registry_factory: RuntimeFactory | None = None,
        contract_provider_factory: RuntimeFactory | None = None,
        permissions_provider: PermissionsProvider | None = None,
        approved_capabilities_provider: PermissionsProvider | None = None,
        maximum_steps: int = 100,
    ) -> None:
        if not callable(model_gateway_factory):
            raise RuntimeCompositionError(
                "model_gateway_factory must be callable"
            )
        if not callable(capability_dispatcher_factory):
            raise RuntimeCompositionError(
                "capability_dispatcher_factory must be callable"
            )
        if maximum_steps <= 0:
            raise RuntimeCompositionError(
                "maximum_steps must be greater than zero"
            )

        self.model_gateway_factory = model_gateway_factory
        self.capability_dispatcher_factory = capability_dispatcher_factory
        self.operation_registry_factory = (
            operation_registry_factory or self._default_operation_registry
        )
        self.contract_provider_factory = (
            contract_provider_factory or self._default_contract_provider
        )
        self.permissions_provider = permissions_provider or self._no_permissions
        self.approved_capabilities_provider = (
            approved_capabilities_provider or self._no_permissions
        )
        self.maximum_steps = maximum_steps

    def compose(self, entry: AgentCatalogEntry) -> ComposedAgentRuntime:
        """Compose one executable runtime from a catalog entry."""

        model_gateway = self.model_gateway_factory(entry)
        capability_dispatcher = self.capability_dispatcher_factory(entry)
        operation_registry = self.operation_registry_factory(entry)
        contract_provider = self.contract_provider_factory(entry)

        if model_gateway is None:
            raise RuntimeCompositionError("model gateway factory returned None")
        if capability_dispatcher is None:
            raise RuntimeCompositionError(
                "capability dispatcher factory returned None"
            )
        if operation_registry is None:
            raise RuntimeCompositionError(
                "operation registry factory returned None"
            )
        if contract_provider is None:
            raise RuntimeCompositionError(
                "contract provider factory returned None"
            )

        context = ExecutionContext(
            model_gateway=model_gateway,
            contract_provider=contract_provider,
            capability_dispatcher=capability_dispatcher,
            operation_registry=operation_registry,
            permissions=frozenset(self.permissions_provider(entry)),
            approved_capabilities=frozenset(
                self.approved_capabilities_provider(entry)
            ),
        )

        engine = WorkflowEngine(
            bundle=entry.bundle,
            context=context,
            maximum_steps=self.maximum_steps,
        )

        return ComposedAgentRuntime(
            entry=entry,
            contract_provider=contract_provider,
            operation_registry=operation_registry,
            capability_dispatcher=capability_dispatcher,
            execution_context=context,
            workflow_engine=engine,
        )

    @staticmethod
    def _default_operation_registry(
        entry: AgentCatalogEntry,
    ) -> OperationRegistry:
        del entry
        return OperationRegistry()

    @staticmethod
    def _default_contract_provider(
        entry: AgentCatalogEntry,
    ) -> ContractProviderAdapter:
        return ContractProviderAdapter(
            ContractFactory(entry.bundle)
        )

    @staticmethod
    def _no_permissions(entry: AgentCatalogEntry) -> Collection[str]:
        del entry
        return ()
