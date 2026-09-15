"""Framework-neutral registry for governed Analytics Foundation capabilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel

from AnalyticsFoundation import session_memory


class CreateWorkspaceRequest(BaseModel):
    pass


class AddFiltersRequest(BaseModel):
    workspace_id: str
    filters: dict[str, Any]


class RegisterDatasetRequest(BaseModel):
    workspace_id: str
    dataset: str
    table: str


class ReadTrendsRequest(BaseModel):
    table: str | None = None
    connection_info: dict[str, Any] | None = None


class ReadWafersRequest(BaseModel):
    table: str | None = None
    connection_info: dict[str, Any] | None = None


class GetConnectionInfoRequest(BaseModel):
    workspace_id: str


class DatabaseExistsRequest(BaseModel):
    database_name: str


class CreateDatabaseRequest(BaseModel):
    database_name: str


class GetTableNamesRequest(BaseModel):
    database_name: str


class CreateTablesRequest(BaseModel):
    database_name: str
    tables: list[dict[str, Any]]


class ListAssetsRequest(BaseModel):
    type: str | None = None
    name: str | None = None
    sharing: str | None = None


class GetAssetRequest(BaseModel):
    asset_id: str


class AddAssetRequest(BaseModel):
    name: str
    type: str
    description: str | None = None
    sharing: str = "private"
    metadata: dict[str, Any] | None = None


class DeleteAssetRequest(BaseModel):
    asset_id: str


class ListProcessingRequest(BaseModel):
    workspace_id: str
    service_name: str | None = None
    service_version: str | None = None


class CreateProcessingRequest(BaseModel):
    workspace_id: str
    service_name: str
    service_version: str
    display_name: str | None = None


class GetProcessingRequest(BaseModel):
    workspace_id: str
    instance_id: str


class StopProcessingRequest(BaseModel):
    workspace_id: str
    instance_id: str


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    description: str
    request_model: Type[BaseModel]
    required_permissions: tuple[str, ...]
    requires_approval: bool
    side_effect: bool
    owner: str = "Analytics Foundation"
    version: str = "1.0"

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "input_schema": self.request_model.model_json_schema(),
            "required_permissions": list(self.required_permissions),
            "requires_approval": self.requires_approval,
            "side_effect": self.side_effect,
            "owner": self.owner,
        }


@dataclass(frozen=True)
class _RegisteredCapability:
    definition: CapabilityDefinition
    handler: Callable[..., Any]


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, _RegisteredCapability] = {}

    def register(self, definition: CapabilityDefinition, handler: Callable[..., Any]) -> None:
        self._capabilities[definition.name] = _RegisteredCapability(definition, handler)

    def get(self, name: str) -> CapabilityDefinition:
        try:
            return self._capabilities[name].definition
        except KeyError as exc:
            raise KeyError(f"Unknown Analytics Foundation capability: {name}") from exc

    def list(self) -> list[dict[str, Any]]:
        return [item.definition.metadata() for item in self._capabilities.values()]

    def invoke(
        self,
        name: str,
        *,
        permissions: set[str] | None = None,
        approved: bool = False,
        **kwargs: Any,
    ) -> Any:
        try:
            registered = self._capabilities[name]
        except KeyError as exc:
            raise KeyError(f"Unknown Analytics Foundation capability: {name}") from exc

        definition = registered.definition
        granted = permissions or set()
        missing = set(definition.required_permissions) - granted
        if missing:
            raise PermissionError(
                f"Capability {name} requires permissions: {', '.join(sorted(missing))}"
            )
        if definition.requires_approval and not approved:
            session_memory.record_event(
                "capability_denied",
                {"capability": name, "reason": "human_approval_required"},
            )
            raise PermissionError(f"Capability {name} requires human approval")

        request = definition.request_model.model_validate(kwargs)
        payload = {"capability": name, "version": definition.version, "arguments": request.model_dump()}
        session_memory.record_event("tool_invocation", payload)
        started = time.perf_counter()
        try:
            result = registered.handler(**request.model_dump())
        except Exception as exc:
            session_memory.record_event(
                "tool_result",
                {**payload, "status": "error", "error": str(exc)},
                duration_ms=(time.perf_counter() - started) * 1000,
            )
            raise

        session_memory.record_event(
            "tool_result",
            {**payload, "status": "success", "result": result},
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return result


def _build_default_registry() -> CapabilityRegistry:
    from AnalyticsFoundation import (
        assets_client,
        datawarehouse,
        lanadb_query,
        processing_client,
        query_engine_client,
        workspace_client,
    )

    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            name="workspace.create",
            description="Create an Analytics Foundation workspace.",
            request_model=CreateWorkspaceRequest,
            required_permissions=("workspace:create",),
            requires_approval=False,
            side_effect=True,
        ),
        workspace_client.create_workspace,
    )
    registry.register(
        CapabilityDefinition(
            name="workspace.add_filters",
            description="Apply application-selected filters to a workspace.",
            request_model=AddFiltersRequest,
            required_permissions=("workspace:write",),
            requires_approval=False,
            side_effect=True,
        ),
        workspace_client.add_filters,
    )
    registry.register(
        CapabilityDefinition(
            name="workspace.register_dataset",
            description="Register a dataset/table in a workspace; may provision compute.",
            request_model=RegisterDatasetRequest,
            required_permissions=("workspace:register",),
            requires_approval=True,
            side_effect=True,
        ),
        workspace_client.register,
    )
    registry.register(
        CapabilityDefinition(
            name="workspace.get_connection_info",
            description="Get the JDBC connection info for a workspace's provisioned database.",
            request_model=GetConnectionInfoRequest,
            required_permissions=("workspace:read",),
            requires_approval=False,
            side_effect=False,
        ),
        workspace_client.get_connection_info,
    )
    registry.register(
        CapabilityDefinition(
            name="data_query.read_trends",
            description="Read raw KPI/trend rows from PostgreSQL.",
            request_model=ReadTrendsRequest,
            required_permissions=("query:trends:read",),
            requires_approval=False,
            side_effect=False,
        ),
        lanadb_query.query_trend_rows,
    )
    registry.register(
        CapabilityDefinition(
            name="data_query.read_wafers",
            description="Read raw wafer-level rows from StarRocks.",
            request_model=ReadWafersRequest,
            required_permissions=("query:wafers:read",),
            requires_approval=False,
            side_effect=False,
        ),
        datawarehouse.query_wafer_rows,
    )
    registry.register(
        CapabilityDefinition(
            name="query_engine.database_exists",
            description="Check whether a Query Engine database exists.",
            request_model=DatabaseExistsRequest,
            required_permissions=("query_engine:read",),
            requires_approval=False,
            side_effect=False,
        ),
        query_engine_client.database_exists,
    )
    registry.register(
        CapabilityDefinition(
            name="query_engine.create_database",
            description="Create a Query Engine database for a workspace's selected data.",
            request_model=CreateDatabaseRequest,
            required_permissions=("query_engine:write",),
            requires_approval=True,
            side_effect=True,
        ),
        query_engine_client.create_database,
    )
    registry.register(
        CapabilityDefinition(
            name="query_engine.get_table_names",
            description="List table names in a Query Engine database.",
            request_model=GetTableNamesRequest,
            required_permissions=("query_engine:read",),
            requires_approval=False,
            side_effect=False,
        ),
        query_engine_client.get_table_names,
    )
    registry.register(
        CapabilityDefinition(
            name="query_engine.create_tables",
            description="Create tables in a Query Engine database.",
            request_model=CreateTablesRequest,
            required_permissions=("query_engine:write",),
            requires_approval=True,
            side_effect=True,
        ),
        query_engine_client.create_tables,
    )
    registry.register(
        CapabilityDefinition(
            name="asset.list",
            description="List accessible assets and their platform metadata.",
            request_model=ListAssetsRequest,
            required_permissions=("asset:read",),
            requires_approval=False,
            side_effect=False,
        ),
        assets_client.list_assets,
    )
    registry.register(
        CapabilityDefinition(
            name="asset.get",
            description="Retrieve a single asset by id.",
            request_model=GetAssetRequest,
            required_permissions=("asset:read",),
            requires_approval=False,
            side_effect=False,
        ),
        assets_client.get_asset,
    )
    registry.register(
        CapabilityDefinition(
            name="asset.add",
            description="Upload a new asset with metadata.",
            request_model=AddAssetRequest,
            required_permissions=("asset:write",),
            requires_approval=False,
            side_effect=True,
        ),
        assets_client.add_asset,
    )
    registry.register(
        CapabilityDefinition(
            name="asset.delete",
            description="Delete an asset by id.",
            request_model=DeleteAssetRequest,
            required_permissions=("asset:write",),
            requires_approval=True,
            side_effect=True,
        ),
        assets_client.delete_asset,
    )
    registry.register(
        CapabilityDefinition(
            name="processing.list",
            description="List processing instances for a workspace.",
            request_model=ListProcessingRequest,
            required_permissions=("processing:read",),
            requires_approval=False,
            side_effect=False,
        ),
        processing_client.list_processing_instances,
    )
    registry.register(
        CapabilityDefinition(
            name="processing.create",
            description="Enqueue a processing instance for a workspace; provisions compute.",
            request_model=CreateProcessingRequest,
            required_permissions=("processing:write",),
            requires_approval=True,
            side_effect=True,
        ),
        processing_client.create_processing_instance,
    )
    registry.register(
        CapabilityDefinition(
            name="processing.get",
            description="Retrieve a processing instance by id.",
            request_model=GetProcessingRequest,
            required_permissions=("processing:read",),
            requires_approval=False,
            side_effect=False,
        ),
        processing_client.get_processing_instance,
    )
    registry.register(
        CapabilityDefinition(
            name="processing.stop",
            description="Stop a running processing instance.",
            request_model=StopProcessingRequest,
            required_permissions=("processing:write",),
            requires_approval=True,
            side_effect=True,
        ),
        processing_client.stop_processing_instance,
    )
    return registry


registry = _build_default_registry()


def list_capabilities() -> list[dict[str, Any]]:
    return registry.list()


def invoke(
    name: str,
    *,
    permissions: set[str] | None = None,
    approved: bool = False,
    **kwargs: Any,
) -> Any:
    return registry.invoke(name, permissions=permissions, approved=approved, **kwargs)
