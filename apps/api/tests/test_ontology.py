"""The ontology grounds the agents and supplies the protected purposes to the decision rules."""

import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from engines.agents.gateway import AgentRequest, AgentResult
from engines.agents.pipeline import AGENTS, checked_content
from engines.decision.rules import PROTECTED_WORDS
from engines.ontology.ontology import concepts, grounding_for, protected_patterns

CONSULTANT = {"X-Studio-Persona": "consultant"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/workspace/reset")
        yield test_client
        test_client.post("/api/workspace/reset")


def test_every_relation_points_at_a_real_concept() -> None:
    known = concepts()
    targets = {r["target"] for concept in known.values() for r in concept.get("relations", [])}
    assert targets <= set(known)


def test_the_protected_rule_comes_from_the_ontology_unchanged() -> None:
    assert protected_patterns() == ["year-end", r"\baudit", "statutory", r"\btax\b"]
    assert PROTECTED_WORDS.pattern == r"year-end|\baudit|statutory|\btax\b"
    assert PROTECTED_WORDS.flags & re.IGNORECASE


def test_grounding_finds_concepts_and_their_neighbours() -> None:
    found = {concept["id"] for concept in grounding_for("Write-downs above the threshold")}
    assert {"write_down", "approval_rule"} <= found
    assert "billing_adjustment" in found, "a related concept comes with it"


def test_grounding_matches_whole_terms_only() -> None:
    assert grounding_for("attaxed syntax") == []


def test_the_prepared_artefacts_name_real_concepts(client: TestClient) -> None:
    rows = client.get("/api/artefacts/CC-014").json()
    named = next(row for row in rows if row["kind"] == "code_explanation")["content"]["ontology_concepts"]
    assert "write_down" in named


def test_an_agent_cannot_cite_a_concept_it_was_not_given() -> None:
    spec = next(entry for entry in AGENTS if entry.agent == "code_explainer")
    output = {
        "plain_english": "x",
        "purpose_known": True,
        "steps": [],
        "hidden_rules": [],
        "cloud_blockers": [],
    }
    payload = {"ontology": [{"id": "write_down"}], "source_text": ""}
    request = AgentRequest("code_explainer", "CC-014", "1", payload)
    good = AgentResult({**output, "ontology_concepts": ["write_down"]}, "live_model", None, 1)
    assert checked_content(spec, request, good)["ontology_concepts"] == ["write_down"]
    bad = AgentResult({**output, "ontology_concepts": ["invented"]}, "live_model", None, 1)
    with pytest.raises(ValueError):
        checked_content(spec, request, bad)


def test_the_ontology_is_available_to_the_screens(client: TestClient) -> None:
    body = client.get("/api/ontology", headers=CONSULTANT).json()
    assert body["concepts"]["write_down"]["label"] == "Write-down"
