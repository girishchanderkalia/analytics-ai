"""Processing API client (platform capability).

Stands in for Analytics Foundation's Processing API: enqueue, inspect, and stop
processing instances (e.g. recipe/service execution) for a workspace. Backed by an
in-memory stub today; a real deployment would call the endpoints in
``apis/api.yml`` (processing tag) instead.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

_instances: dict[str, dict[str, Any]] = {}


def list_processing_instances(
    workspace_id: str,
    service_name: str | None = None,
    service_version: str | None = None,
) -> list[dict[str, Any]]:
    results = [i for i in _instances.values() if i["workspaceId"] == workspace_id]
    if service_name:
        results = [i for i in results if i["serviceName"] == service_name]
    if service_version:
        results = [i for i in results if i["serviceVersion"] == service_version]
    return results


def create_processing_instance(
    workspace_id: str,
    service_name: str,
    service_version: str,
    display_name: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    instance = {
        "id": f"PROC-{uuid.uuid4().hex[:8].upper()}",
        "workspaceId": workspace_id,
        "serviceName": service_name,
        "serviceVersion": service_version,
        "displayName": display_name,
        "status": "queued",
        "progressPercentage": 0.0,
        "progressMessage": "Queued",
        "createdAt": now,
        "startedAt": None,
        "finishedAt": None,
    }
    _instances[instance["id"]] = instance
    return instance


def get_processing_instance(workspace_id: str, instance_id: str) -> dict[str, Any]:
    try:
        instance = _instances[instance_id]
    except KeyError as exc:
        raise KeyError(f"Unknown processing instance: {instance_id}") from exc
    if instance["workspaceId"] != workspace_id:
        raise KeyError(f"Processing instance {instance_id} does not belong to workspace {workspace_id}")
    return instance


def stop_processing_instance(workspace_id: str, instance_id: str) -> dict[str, Any]:
    instance = get_processing_instance(workspace_id, instance_id)
    instance["status"] = "stopped"
    instance["finishedAt"] = datetime.now(timezone.utc).isoformat()
    return instance
