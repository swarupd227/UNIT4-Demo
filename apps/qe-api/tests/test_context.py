from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import get_settings
from app.context import analysis
from app.db import get_engine
from app.main import app
from qe.engines.agents.gateway import AgentRequest
from qe.engines.analysis import CheckFailed, Sources, checked

client = TestClient(app)
SETTINGS = get_settings()
KEY = yaml.safe_load((Path(SETTINGS.answer_key) / "answer_key.yaml").read_text(encoding="utf-8"))
DEFECT_KEY = yaml.safe_load((Path(SETTINGS.answer_key) / "defects.yaml").read_text(encoding="utf-8"))
CASE_KEY = yaml.safe_load((Path(SETTINGS.answer_key) / "manual_cases.yaml").read_text(encoding="utf-8"))
SRC = Sources.at(Path(SETTINGS.estate_root).parent, Path(SETTINGS.history_repo), SETTINGS.gate_percent)


def _agreement(found: dict[str, Any], expected: dict[str, Any]) -> float:
    return sum(1 for key, rule in expected.items() if found.get(key) == rule) / len(expected)


def test_coverage_matches_the_answer_key() -> None:
    body = client.get("/api/coverage").json()
    assert body["summary"]["covered"] == KEY["gate"]["baseline_covered"]
    assert (body["summary"]["critical_covered"], body["summary"]["percent"]) == (7, 58)
    br11 = next(rule for rule in body["rules"] if rule["rule"] == "BR-11")
    assert (br11["caught"], len(br11["faults"]), br11["covered"]) == (1, 3, False)
    flaky = {test["title"][:5] for rule in body["rules"] for test in rule["tests"] if test["flaky"]}
    assert flaky == {"BR-01", "BR-09"}


def test_agents_map_cases_and_defects_like_the_answer_key() -> None:
    result = analysis()
    cases = {c["case_id"]: c["rule"] for c in result["case_mapping"]["content"]["cases"]}
    assert _agreement(cases, {str(c["id"]): c["rule"] for c in CASE_KEY["cases"]}) >= 0.9
    # The key leaves a rule out for defects that only touch a rule's screens or wording, where the
    # agent files them by area. Where the key names a rule, the agent must agree.
    defects = {d["defect_id"]: d["rule"] for d in result["defect_mapping"]["content"]["defects"]}
    named = {d["id"]: d["rule"] for d in DEFECT_KEY["defects"] if d["rule"]}
    assert _agreement(defects, named) >= 0.95
    rounding = {d["id"] for d in DEFECT_KEY["defects"] if d["rule"] == "BR-04"}
    assert {i for i, rule in defects.items() if rule == "BR-04"} == rounding


def test_br04_risk_card_shows_the_rounding_defects() -> None:
    result = analysis()
    facts = next(entry for entry in result["risk_ranking"] if entry["rule"] == "BR-04")
    assert len(facts["defects"]) == 7
    assert facts["files"] == [("src/Billing.Web/Helpers/RoundingHelper.cs", 7)]
    assert facts["no_test"] == 2
    assert sorted(d["id"] for d in facts["defects"] if d["test"] == "none") == ["BILL-1187", "BILL-1203"]
    assert result["risk_cards"]["BR-04"]["status"] == "ok"
    assert result["risk_ranking"][0]["rule"] in {"BR-04", "BR-07"}


def test_the_write_down_approval_is_found_in_code_only() -> None:
    # The finder may report the limit and who approves as two parts of the one approval rule, and
    # nothing else in the module is hidden.
    rules = analysis()["hidden_rules"]["content"]["rules"]
    assert rules and all(rule["related_rule"] == "BR-07" and not rule["documented"] for rule in rules)
    limit = [
        rule
        for rule in rules
        if any(
            c["file"].endswith("AdjustmentService.cs") and "WD_LIMIT = 0.10m" in c["text"]
            for c in rule["citations"]
        )
    ]
    assert len(limit) == 1
    assert "write_down" in limit[0]["ontology_concepts"]


def test_dead_code_matches_the_answer_key() -> None:
    names = {item["name"] for item in analysis()["dead_code"]}
    assert names == set(KEY["planted"]["T10"]["unreachable"])


def _finder_request(rule: dict[str, Any]) -> tuple[AgentRequest, dict[str, Any]]:
    payload = {"code": {"Billing.Web/Services/AdjustmentService.cs": "const decimal WD_LIMIT = 0.10m;\n"}}
    return AgentRequest("hidden_rule_finder", "t", "1", payload), {"rules": [rule]}


def _hidden(**changes: Any) -> dict[str, Any]:
    return {
        "title": "Large write-downs need approval",
        "statement": "s",
        "related_rule": "BR-07",
        "citations": [{"file": "Billing.Web/Services/AdjustmentService.cs", "find": "WD_LIMIT = 0.10m"}],
        "why_hidden": "w",
        "search_phrases": ["manager approval"],
        "proposed_test": "p",
        "ontology_concepts": [],
        **changes,
    }


def test_checks_reject_a_citation_that_is_not_in_the_code() -> None:
    request, output = _finder_request(_hidden())
    assert checked(SRC, request, output)["rules"][0]["citations"][0]["line"] == 1
    for bad in (
        _hidden(
            citations=[{"file": "Billing.Web/Services/AdjustmentService.cs", "find": "WD_LIMIT = 0.15m"}]
        ),
        _hidden(citations=[{"file": "Billing.Web/Services/Other.cs", "find": "WD_LIMIT"}]),
        _hidden(search_phrases=["approval"]),
        _hidden(related_rule="BR-99"),
        _hidden(ontology_concepts=["write_down"]),
    ):
        request, output = _finder_request(bad)
        with pytest.raises(CheckFailed):
            checked(SRC, request, output)


def test_checks_reject_a_risk_card_citing_a_defect_it_was_not_given() -> None:
    request = AgentRequest("risk_analyst", "BR-04", "1", {"defects": [{"id": "BILL-1046"}], "ontology": []})
    card = {
        "headline": "h",
        "what_keeps_breaking": [{"point": "p", "defects": ["BILL-1046", "BILL-1001"]}],
        "why_it_escapes": "w",
        "proposed_tests": [],
        "ontology_concepts": [],
    }
    with pytest.raises(CheckFailed):
        checked(SRC, request, card)


@pytest.fixture
def entry() -> Any:
    entry_id = "TEST-ENTRY"
    started = datetime.now(UTC)
    with get_engine().begin() as db:
        db.execute(
            text("""
                INSERT INTO qe.context_entry (entry_id, kind, title, content, provenance, source)
                VALUES (:id, 'dead_code', 'Test entry', '{}', 'verified_by_code', 'reachability')
            """),
            {"id": entry_id},
        )
    yield entry_id
    with get_engine().begin() as db:
        db.execute(text("DELETE FROM qe.context_entry WHERE entry_id = :id"), {"id": entry_id})
        db.execute(
            text("DELETE FROM qe.audit_event WHERE item_id = :id AND at >= :at"),
            {"id": entry_id, "at": started},
        )


def test_an_engineer_approves_an_entry_and_only_approved_entries_export(entry: str) -> None:
    url = f"/api/context/{entry}/review"
    assert (
        client.post(url, json={"person_key": "full_circuit_owner", "decision": "approved"}).status_code == 403
    )
    assert client.post(url, json={"person_key": "engineer", "decision": "rejected"}).status_code == 422
    assert entry not in {e["id"] for e in client.get("/api/context/export").json()["entries"]}
    assert client.post(url, json={"person_key": "engineer", "decision": "approved"}).status_code == 200
    assert client.post(url, json={"person_key": "engineer", "decision": "approved"}).status_code == 409
    exported = {e["id"]: e for e in client.get("/api/context/export").json()["entries"]}
    assert exported[entry]["approved_by"] == "Ravi Menon"
