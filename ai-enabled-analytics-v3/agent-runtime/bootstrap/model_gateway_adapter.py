"""Execution-model gateway backed by the platform Model Gateway."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any


AgentFactory = Callable[..., Any]


class ModelGatewayBootstrapError(RuntimeError):
    """Raised when the fixed platform Model Gateway cannot be loaded."""


class PlatformModelGateway:
    """Adapt the fixed platform model to the Workflow Engine interface."""

    def __init__(
        self,
        model: Any | None = None,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self.model = (
            model
            if model is not None
            else _load_platform_model()
        )

        self.agent_factory = (
            agent_factory
            if agent_factory is not None
            else _default_agent_factory
        )

    def invoke_structured(
        self,
        system_prompt: str,
        input_text: str,
        output_contract: type[Any],
    ) -> Any:
        """Run one typed request and return its validated output."""

        agent = self.agent_factory(
            model=self.model,
            output_type=output_contract,
            system_prompt=system_prompt,
        )

        result = agent.run_sync(input_text)
        output = result.output

        if hasattr(output, "model_dump"):
            return output.model_dump(
                mode="python"
            )

        return output


def create_model_gateway() -> PlatformModelGateway:
    """Create the framework-owned Model Gateway adapter."""

    return PlatformModelGateway(
        model=_load_platform_model()
    )


def _load_platform_model() -> Any:
    """Load the existing fixed platform model lazily."""

    try:
        module = import_module(
            "foundation.model_gateway"
        )
    except ModuleNotFoundError as exc:
        raise ModelGatewayBootstrapError(
            "Cannot import foundation.model_gateway. "
            "Ensure the repository root containing the "
            "'foundation' package is on PYTHONPATH."
        ) from exc

    get_model = getattr(
        module,
        "get_model",
        None,
    )

    if not callable(get_model):
        raise ModelGatewayBootstrapError(
            "foundation.model_gateway must expose "
            "a callable get_model()"
        )

    return get_model()


def _default_agent_factory(
    **kwargs: Any,
) -> Any:
    """Create a PydanticAI Agent lazily."""

    try:
        module = import_module(
            "pydantic_ai"
        )
    except ModuleNotFoundError as exc:
        raise ModelGatewayBootstrapError(
            "pydantic-ai is required for real "
            "Model Gateway execution"
        ) from exc

    agent_class = getattr(
        module,
        "Agent",
        None,
    )

    if agent_class is None:
        raise ModelGatewayBootstrapError(
            "pydantic_ai must expose Agent"
        )

    return agent_class(**kwargs)