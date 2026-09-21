"""Convert runtime-domain results to API response models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from .models import ExecutionResponse


def _plain_value(value: Any) -> Any:
    """Convert enums and dataclasses into JSON-compatible values."""

    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value):
        return {
            key: _plain_value(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, Mapping):
        return {
            str(key): _plain_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_plain_value(item) for item in value]

    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]

    return value


def execution_response(hosted_result: Any) -> ExecutionResponse:
    """Create an API response from HostedExecutionResult."""

    result = hosted_result.result
    approval_request = _plain_value(result.approval_request)

    return ExecutionResponse(
        agent_id=hosted_result.agent_id,
        agent_version=hosted_result.agent_version,
        status=str(_plain_value(result.status)),
        state=_plain_value(result.state),
        current_node=result.current_node,
        approval_request=approval_request,
        error=result.error,
    )
