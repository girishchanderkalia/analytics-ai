"""Load and validate application-agent definitions from Markdown front matter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFINITION_DIR = (
    Path(__file__).resolve().parents[2]
    / "ai-enabled-analytics-v2"
    / "ai_Agents"
    / "opo-monitoring"
    / "definitions"
)
REQUIRED_DEFINITIONS = {
    "agent-definition.md": "agent",
    "workflow-definition.md": "workflow",
    "knowledge-model.md": "knowledge-model",
    "tools-and-capabilities.md": "tools-and-capabilities",
    "state-model.md": "state-model",
    "sequence-diagrams.md": "sequence-diagrams",
}


@dataclass(frozen=True)
class MarkdownDefinition:
    path: Path
    metadata: dict[str, Any]
    markdown: str


def _split_front_matter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} must start with YAML front matter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError(f"{path} has unclosed YAML front matter") from exc

    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{path} front matter must be a YAML mapping")
    return metadata, "\n".join(lines[end + 1 :])


def load_definitions(definition_dir: Path | None = None) -> dict[str, MarkdownDefinition]:
    """Load the complete application definition bundle from Markdown files."""
    directory = definition_dir or DEFINITION_DIR
    definitions: dict[str, MarkdownDefinition] = {}
    for filename, expected_kind in REQUIRED_DEFINITIONS.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing application definition: {path}")
        metadata, markdown = _split_front_matter(path)
        for key in ("id", "version", "kind"):
            if not metadata.get(key):
                raise ValueError(f"{path} is missing front matter field '{key}'")
        if metadata["kind"] != expected_kind:
            raise ValueError(
                f"{path} has kind {metadata['kind']!r}; expected {expected_kind!r}"
            )
        definitions[filename] = MarkdownDefinition(path, metadata, markdown)

    agent = definitions["agent-definition.md"].metadata
    if not isinstance(agent.get("models"), dict) or not agent["models"]:
        raise ValueError("agent-definition.md must declare at least one model")
    if not isinstance(agent.get("prompts"), dict):
        raise ValueError("agent-definition.md prompts must be a mapping")
    workflow = definitions["workflow-definition.md"].metadata
    if not isinstance(workflow.get("nodes"), list) or not workflow["nodes"]:
        raise ValueError("workflow-definition.md must declare at least one node")
    if not workflow.get("edges"):
        raise ValueError("workflow-definition.md must declare workflow edges")
    state = definitions["state-model.md"].metadata
    if not state.get("fields"):
        raise ValueError("state-model.md must declare state fields")
    tools = definitions["tools-and-capabilities.md"].metadata
    if not tools.get("capabilities"):
        raise ValueError("tools-and-capabilities.md must declare capabilities")
    return definitions


_DEFINITIONS: dict[str, MarkdownDefinition] | None = None


def get_definitions() -> dict[str, MarkdownDefinition]:
    global _DEFINITIONS
    if _DEFINITIONS is None:
        _DEFINITIONS = load_definitions()
    return _DEFINITIONS
