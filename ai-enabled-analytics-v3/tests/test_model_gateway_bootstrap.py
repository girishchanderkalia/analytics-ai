"""Tests for fixed Model Gateway bootstrap wiring."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


V3_ROOT = Path(__file__).resolve().parents[1]
AGENT_RUNTIME_ROOT = V3_ROOT / "agent-runtime"

if str(AGENT_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_RUNTIME_ROOT))


from bootstrap.model_gateway_adapter import (  # noqa: E402
    PlatformModelGateway,
)


@dataclass
class FakeContract:
    finding: str

    def model_dump(self, mode: str) -> dict[str, str]:
        assert mode == "python"
        return {"finding": self.finding}


class FakeRunResult:
    def __init__(self, output: Any) -> None:
        self.output = output


class FakeAgent:
    def __init__(
        self,
        model: Any,
        output_type: type[Any],
        system_prompt: str,
    ) -> None:
        self.model = model
        self.output_type = output_type
        self.system_prompt = system_prompt
        self.inputs: list[str] = []

    def run_sync(self, input_text: str) -> FakeRunResult:
        self.inputs.append(input_text)
        return FakeRunResult(FakeContract(finding="Typed result"))


class CapturingAgentFactory:
    def __init__(self) -> None:
        self.instances: list[FakeAgent] = []

    def __call__(self, **kwargs: Any) -> FakeAgent:
        agent = FakeAgent(**kwargs)
        self.instances.append(agent)
        return agent


def test_gateway_builds_typed_agent() -> None:
    factory = CapturingAgentFactory()
    model = object()
    gateway = PlatformModelGateway(
        model=model,
        agent_factory=factory,
    )

    response = gateway.invoke_structured(
        system_prompt="Use application knowledge",
        input_text="Show recent trends",
        output_contract=FakeContract,
    )

    assert response == {"finding": "Typed result"}
    assert len(factory.instances) == 1
    assert factory.instances[0].model is model
    assert factory.instances[0].output_type is FakeContract
    assert factory.instances[0].system_prompt == (
        "Use application knowledge"
    )
    assert factory.instances[0].inputs == ["Show recent trends"]


def test_gateway_returns_non_pydantic_output_unchanged() -> None:
    class PlainAgent(FakeAgent):
        def run_sync(self, input_text: str) -> FakeRunResult:
            return FakeRunResult({"value": input_text})

    gateway = PlatformModelGateway(
        model=object(),
        agent_factory=lambda **kwargs: PlainAgent(**kwargs),
    )

    response = gateway.invoke_structured(
        system_prompt="System",
        input_text="Input",
        output_contract=FakeContract,
    )

    assert response == {"value": "Input"}
