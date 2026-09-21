"""Generic interpreter for fully declarative Markdown agent definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from .definition_loader import MarkdownDefinition, get_definitions


@dataclass(frozen=True)
class WorkflowNode:
    id: str
    type: str
    prompt: str | None = None
    output: str | None = None
    capability: str | None = None
    approval: str | None = None
    decision_field: str | None = None


@dataclass(frozen=True)
class CapabilityPolicy:
    id: str
    operation: str
    permissions: tuple[str, ...]
    side_effect: bool
    approval_required: bool


class DeclarativeAgent:
    """Load definitions and interpret workflow nodes without agent-specific handlers."""

    def __init__(self, definitions: dict[str, MarkdownDefinition] | None = None, dispatcher: Any = None):
        self.definitions = definitions or get_definitions()
        self.agent = self.definitions["agent-definition.md"].metadata
        self.workflow = self.definitions["workflow-definition.md"].metadata
        self.state = self.definitions["state-model.md"].metadata
        self.tools = self.definitions["tools-and-capabilities.md"].metadata
        self.knowledge = self.definitions["knowledge-model.md"]
        self.sequences = self.definitions["sequence-diagrams.md"]
        from .contract_factory import build_contracts

        self.contracts = build_contracts(self.definitions)
        self.dispatcher = dispatcher
        self._validate()

    def _validate(self) -> None:
        node_ids = {node.get("id") for node in self.workflow.get("nodes", [])}
        if not node_ids or self.workflow.get("entry_node") not in node_ids:
            raise ValueError("workflow must declare a valid entry node")
        if None in node_ids or len(node_ids) != len(self.workflow["nodes"]):
            raise ValueError("workflow nodes must have unique IDs")
        valid_types = {"model", "capability", "approval"}
        capability_ids = {capability["id"] for capability in self.tools.get("capabilities", [])}
        for node in self.workflow["nodes"]:
            if node.get("type") not in valid_types:
                raise ValueError(f"unsupported declarative node type: {node.get('type')}")
            if node["type"] == "model" and node.get("prompt") not in self.agent.get("prompts", {}):
                raise ValueError(f"model node references unknown prompt: {node}")
            if node["type"] == "model" and node.get("output") not in self.agent.get("models", {}):
                raise ValueError(f"model node references unknown output: {node}")
            if node["type"] == "capability" and node.get("capability") not in capability_ids:
                raise ValueError(f"node references unknown capability: {node}")
            if node["type"] == "approval" and not node.get("approval"):
                raise ValueError(f"approval node must declare an approval payload type: {node}")
        for edge in self.workflow.get("edges", []):
            if edge["from"] not in node_ids or edge["to"] not in node_ids | {"END"}:
                raise ValueError(f"workflow edge references an unknown node: {edge}")
        if not self.state.get("fields"):
            raise ValueError("state definition must declare fields")

    @property
    def nodes(self) -> tuple[WorkflowNode, ...]:
        return tuple(
            WorkflowNode(
                node["id"], node["type"], node.get("prompt"), node.get("output"),
                node.get("capability"), node.get("approval"), node.get("decision_field"),
            )
            for node in self.workflow["nodes"]
        )

    @property
    def capabilities(self) -> tuple[CapabilityPolicy, ...]:
        return tuple(
            CapabilityPolicy(
                item["id"], item["operation"], tuple(item.get("permissions", [])),
                bool(item.get("side_effect", False)), bool(item.get("approval_required", False)),
            )
            for item in self.tools.get("capabilities", [])
        )

    def capability(self, capability_id: str) -> CapabilityPolicy:
        for capability in self.capabilities:
            if capability.id == capability_id:
                return capability
        raise KeyError(f"Unknown declarative capability: {capability_id}")

    def authorize(self, capability_id: str, *, permissions: set[str], approved: bool = False) -> None:
        capability = self.capability(capability_id)
        missing = set(capability.permissions) - permissions
        if missing:
            raise PermissionError(f"Missing permissions for {capability_id}: {sorted(missing)}")
        if capability.approval_required and not approved:
            raise PermissionError(f"Capability {capability_id} requires approval")

    def build_graph(self):
        from langgraph.graph import END, START, StateGraph

        state_type = TypedDict(
            "DeclarativeAgentState",
            {name: object for name in self.state.get("fields", {})},
            total=False,
        )
        builder = StateGraph(state_type)
        for node in self.nodes:
            builder.add_node(node.id, lambda state, node=node: self.execute(node, state))
        builder.add_edge(START, self.workflow["entry_node"])

        outgoing: dict[str, list[str]] = {}
        for edge in self.workflow.get("edges", []):
            if edge["to"] == "END":
                continue
            outgoing.setdefault(edge["from"], []).append(edge["to"])
        routing = self.workflow.get("routing", {})
        conditions = routing.get("conditions", [])
        for source, targets in outgoing.items():
            source_conditions = [item for item in conditions if item.get("from") == source]
            if source_conditions:
                fallback = routing.get("defaults", {}).get(source, targets[0])
                destinations = {item["to"]: (END if item["to"] == "END" else item["to"]) for item in source_conditions}
                destinations[fallback] = END if fallback == "END" else fallback
                builder.add_conditional_edges(source, lambda state, source=source: self.route(source, state), destinations)
            else:
                builder.add_edge(source, targets[0])
        for node in self.nodes:
            if node.id not in outgoing:
                builder.add_edge(node.id, END)
        return builder.compile()

    def execute(self, node: WorkflowNode, state: dict[str, Any]) -> dict[str, Any]:
        if node.type == "model":
            from .model_runtime import run_structured

            result = run_structured(
                f"{self.agent['prompts'][node.prompt]}\n\n{self.knowledge.markdown}",
                self.contracts[node.output],
                str(state),
            )
            return {node.output: result.model_dump()}
        if node.type == "capability":
            if self.dispatcher is None:
                raise RuntimeError(f"No capability dispatcher configured for {node.capability}")
            return self.dispatcher.invoke(node.capability, state)
        if node.type == "approval":
            from langgraph.types import interrupt

            decision = interrupt({"type": node.approval, "state": state})
            decision_field = node.decision_field or f"{node.id}_approved"
            return {decision_field: bool(decision)}
        raise ValueError(f"Unsupported declarative node type: {node.type}")

    def route(self, source: str, state: dict[str, Any]) -> str:
        for condition in self.workflow.get("routing", {}).get("conditions", []):
            if condition.get("from") == source and _matches(condition["when"], state):
                return condition["to"]
        return self.workflow.get("routing", {}).get("defaults", {}).get(source, "END")


def _matches(expression: str, state: dict[str, Any]) -> bool:
    field, operator, expected = expression.split(" ", 2)
    actual = state.get(field)
    value = None if expected == "null" else [] if expected == "[]" else expected.strip("'\"")
    if operator == "==":
        return actual == value
    if operator == "!=":
        return actual != value
    raise ValueError(f"Unsupported declarative routing operator: {operator}")
