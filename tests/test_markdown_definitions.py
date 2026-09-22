from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-enabled-analytics-v2"))

from agent_runtime.definition_loader import load_definitions  # noqa: E402
from agent_runtime.declarative_runtime import DeclarativeAgent  # noqa: E402
from agent_runtime.contract_factory import (  # noqa: E402
    DetectionScope,
    FindingsSummary,
    TrendFilters,
)


def test_all_markdown_definitions_load():
    definitions = load_definitions(
        ROOT
        / "ai-enabled-analytics-v2"
        / "ai_Agents"
        / "opo-monitoring"
        / "definitions"
    )

    assert len(definitions) == 6
    assert definitions["agent-definition.md"].metadata["kind"] == "agent"
    assert definitions["workflow-definition.md"].metadata["max_registration_polls"] == 10


def test_contracts_are_generated_from_agent_definition():
    assert set(TrendFilters.model_fields) == {
        "lookback_days",
        "start_date",
        "end_date",
        "lot_ids",
        "product_ids",
        "layer_ids",
        "exposure_equipment_ids",
        "interpretation",
    }
    assert DetectionScope().mode == "baseline"
    assert FindingsSummary().confidence == "low"


def test_declarative_agent_builds_the_supplied_markdown_bundle():
    definitions = load_definitions(
        ROOT
        / "ai-enabled-analytics-v2"
        / "ai_Agents"
        / "opo-monitoring"
        / "definitions"
    )

    agent = DeclarativeAgent(definitions)
    graph = agent.build_graph()

    assert "Evidence Labels" in agent.knowledge.markdown
    assert "sequenceDiagram" in agent.sequences.markdown
    assert set(graph.get_graph().nodes) == {
        "__start__",
        "__end__",
        "parse_trend_request",
        "analyze_trends",
        "investigate_outlier",
        "summarize_findings",
    }
