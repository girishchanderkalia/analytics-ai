"""Dependency composition for the Application Agent Runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from execution.definition_loader import AgentRepository
from execution.workflow_engine import WorkflowEngine
from persistence.sqlite_conversation_store import SQLiteConversationStore

from .runtime_service import RuntimeService


@dataclass(frozen=True)
class RuntimeDependencies:
    """Externally supplied runtime dependencies."""

    execution_context: Any


def create_runtime_service(
    *,
    repository_root: Path | str,
    database_path: Path | str,
    dependencies: RuntimeDependencies,
    maximum_steps: int = 100,
) -> RuntimeService:
    """Compose the Runtime Service from concrete infrastructure."""

    root = Path(repository_root).resolve()
    agent_repository = AgentRepository(root / "ai-agents")
    conversation_store = SQLiteConversationStore(database_path)

    def engine_factory(bundle: Any) -> WorkflowEngine:
        return WorkflowEngine(
            bundle=bundle,
            context=dependencies.execution_context,
            maximum_steps=maximum_steps,
        )

    return RuntimeService(
        agent_repository=agent_repository,
        conversation_store=conversation_store,
        engine_factory=engine_factory,
    )
