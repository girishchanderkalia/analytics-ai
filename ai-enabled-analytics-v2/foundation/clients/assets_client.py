"""Assets API client (platform capability).

Stands in for Analytics Foundation's Assets API: available assets and their
platform metadata (e.g. recipes, flow definitions), listable, uploadable, and
retrievable per user. Backed by an in-memory stub today; a real deployment would
call the endpoints in ``apis/api.yml`` (asset tag) instead.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

_assets: dict[str, dict[str, Any]] = {}


def list_assets(
    type: str | None = None,
    name: str | None = None,
    sharing: str | None = None,
) -> list[dict[str, Any]]:
    results = list(_assets.values())
    if type:
        results = [asset for asset in results if asset["type"] == type]
    if name:
        results = [asset for asset in results if name.lower() in asset["name"].lower()]
    if sharing:
        results = [asset for asset in results if asset["sharing"] == sharing]
    return results


def get_asset(asset_id: str) -> dict[str, Any]:
    try:
        return _assets[asset_id]
    except KeyError as exc:
        raise KeyError(f"Unknown asset: {asset_id}") from exc


def add_asset(
    name: str,
    type: str,
    description: str | None = None,
    sharing: str = "private",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    asset = {
        "id": f"ASSET-{uuid.uuid4().hex[:8].upper()}",
        "name": name,
        "type": type,
        "description": description,
        "sharing": sharing,
        "metadata": metadata or {},
        "owner": "demo-user",
        "contentType": "application/octet-stream",
        "createdAt": now,
        "updatedAt": now,
    }
    _assets[asset["id"]] = asset
    return asset


def delete_asset(asset_id: str) -> None:
    _assets.pop(asset_id, None)
