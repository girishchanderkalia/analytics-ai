"""Dependency composition for the Application Agent Runtime.

The host layer connects runtime infrastructure without coupling the
definition loader to concrete execution implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from execution.definition_loader import AgentRepository
from execution.operation_registry import (
    OperationRegistry,
    create_default_operation_registry,
)


@dataclass(frozen=True)
class RuntimeComposition:
    """Dependencies required by the Application Agent Runtime."""

    repository_root: Path
    operation_registry: OperationRegistry
    agent_repository: AgentRepository


def create_runtime_composition(
    repository_root: Path | str,
) -> RuntimeComposition:
    """Create the default runtime dependency composition."""

    root = Path(repository_root).resolve()

    if not root.is_dir():
        raise ValueError(
            f"Repository root does not exist: {root}"
        )

    agent_catalog_root = root / "ai-agents"

    if not agent_catalog_root.is_dir():
        raise ValueError(
            f"Agent catalog does not exist: {agent_catalog_root}"
        )

    operation_registry = create_default_operation_registry()

    agent_repository = AgentRepository(
        agent_catalog_root,
        operation_names=operation_registry.names(),
    )

    return RuntimeComposition(
        repository_root=root,
        operation_registry=operation_registry,
        agent_repository=agent_repository,
    )
