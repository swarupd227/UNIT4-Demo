"""Phase 3 exit gates, against the seeded database."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from engines.agents.gateway import AgentRequest, ReplayGateway, ReplayMiss, StaleReplay
from engines.validation.checks import rule_decision

CONSULTANT = {"X-Studio-Persona": "consultant"}
CUSTOMER = {"X-Studio-Persona": "customer"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/workspace/reset")
        yield test_client
        test_client.post("/api/workspace/reset")


def run(client: TestClient) -> dict[str, Any]:
    response = client.post("/api/reconciliation/run")
    assert response.status_code == 200
    return response.json()


def statuses(report: dict[str, Any]) -> dict[str, str]:
    return {check["check_id"]: check["status"] for check in report["checks"]}


def choose_threshold(client: TestClient, percent: int) -> None:
    client.post("/api/decisions/CC-014/ask", headers=CONSULTANT, json={"question": "Which threshold?"})
    client.post("/api/decisions/CC-014/answer", headers=CUSTOMER, json={"answer": f"{percent}%"})


def test_checks_give_the_specified_results(client: TestClient) -> None:
    assert statuses(run(client)) == {
        "R1": "pass",
        "R2": "fail",
        "R3": "pass",
        "R4": "fail",
        "R5": "pass",
        "R6": "fail",
        "R7": "pass",
        "R8": "waiting",
    }


def test_same_input_gives_identical_hashes(client: TestClient) -> None:
    first, second = run(client), run(client)
    assert first["run_id"] != second["run_id"]
    assert first["input_hash"] == second["input_hash"]
    assert first["result_hash"] == second["result_hash"]


def test_a_changed_decision_input_changes_the_hash(client: TestClient) -> None:
    first = run(client)
    choose_threshold(client, 15)
    second = run(client)
    assert first["input_hash"] != second["input_hash"]
    assert first["result_hash"] != second["result_hash"]


def test_receivables_cause_is_proven(client: TestClient) -> None:
    exception = next(e for e in run(client)["exceptions"] if e["check_id"] == "R2")
    assert exception["code"] == "fx_rate_precision"
    assert exception["amount_minor"] == 124050
    assert exception["detail"]["items_recalculated"] > 0
    assert exception["amount_minor"] > exception["detail"]["line_rounding_limit_minor"]
    assert exception["detail"]["target_rates"]["EUR"] == "0.872"


def test_every_difference_row_can_be_drilled_into(client: TestClient) -> None:
    report = run(client)
    for check in report["checks"]:
        rows = client.get(f"/api/reconciliation/{check['check_id']}/differences?limit=1000").json()
        assert len(rows) == min(check["difference_count"], 1000)
    wip = client.get("/api/reconciliation/R4/differences").json()
    assert len(wip) == 14
    assert all(row["detail"]["project_status"] == "closed" for row in wip)


def test_mapping_check_finds_both_problems(client: TestClient) -> None:
    codes = {e["code"] for e in run(client)["exceptions"] if e["check_id"] == "R6"}
    assert codes == {"vat_mapping_conflict", "duplicate_dimension_value"}


def test_parity_explains_the_partner_fix_to_the_penny(client: TestClient) -> None:
    r7 = next(c for c in run(client)["checks"] if c["check_id"] == "R7")
    report = r7["summary"]["reports"][0]
    assert report["cr_total"] == report["faithful_rebuild_total"]
    item = report["reconciling_item"]
    assert report["fixed_rebuild_total"] - report["cr_total"] == item["amount"] > 0
    assert len(item["partners"]) == 6


@pytest.mark.parametrize("percent", [10, 15])
def test_rule_tests_pass_at_either_threshold(client: TestClient, percent: int) -> None:
    choose_threshold(client, percent)
    r8 = next(c for c in run(client)["checks"] if c["check_id"] == "R8")
    assert r8["status"] == "pass"
    assert r8["summary"]["threshold"] == percent
    assert len(r8["summary"]["results"]) == 9


def test_rule_holds_only_above_the_threshold() -> None:
    case = {
        "adjust_type": "write_down",
        "billable_minor": 100000,
        "adjust_minor": 15000,
        "prior_approval": False,
    }
    assert rule_decision(case, 15) == "apply"
    assert rule_decision({**case, "adjust_minor": 15001}, 15) == "hold"
    assert rule_decision(case, 10) == "hold"


def test_artefacts_are_stored_with_honest_provenance_and_real_lines(client: TestClient) -> None:
    artefacts = {a["kind"]: a for a in client.get("/api/artefacts/CC-014").json()}
    assert set(artefacts) == {"code_explanation", "extension_spec", "rule_card", "test_cases"}
    assert all(a["source"] == "hand_authored" and a["duration_ms"] is None for a in artefacts.values())
    source = client.get("/api/decisions/CC-014").json()["source_text"].splitlines()
    for citation in artefacts["rule_card"]["content"]["sources"]:
        assert citation["find"] in source[citation["line"] - 1]


def test_score_meets_the_exit_gate(client: TestClient) -> None:
    run(client)
    result = client.get("/api/score").json()
    assert result["issues"]["found"] == 10, result["issues"]["detail"]
    assert result["false_items"]["count"] <= 3
    assert result["passed"]


def test_score_without_a_run_does_not_pass(client: TestClient) -> None:
    result = client.get("/api/score").json()
    assert result["issues"]["found"] == 6
    assert not result["passed"]


def test_mapping_memory_records_approvals_and_rejections(client: TestClient) -> None:
    client.post("/api/decisions/CC-041/accept", headers=CONSULTANT)
    client.post("/api/decisions/CC-041/accept", headers={"X-Studio-Persona": "unit4_technical"})
    body = {"outcome": "keep_repoint", "reason": "Read-only in practice"}
    client.post("/api/decisions/RP-077/edit", headers=CONSULTANT, json=body)
    memory = client.get("/api/mapping-memory").json()
    assert any(m["item_id"] == "CC-041" and m["review_status"] == "approved" for m in memory)
    assert any(m["item_id"] == "RP-077" and m["review_status"] == "rejected" for m in memory)


def request(payload: dict[str, str]) -> AgentRequest:
    return AgentRequest("agent", "subject", "1", payload)


def test_replay_refuses_a_changed_input(tmp_path: Path) -> None:
    (tmp_path / "agent").mkdir()
    (tmp_path / "agent" / "subject.json").write_text(
        json.dumps(
            {
                "input_hash": request({"a": "1"}).input_hash,
                "source": "hand_authored",
                "model": None,
                "duration_ms": None,
                "output": {},
            }
        )
    )
    gateway = ReplayGateway(tmp_path)
    assert gateway.run(request({"a": "1"})).output == {}
    with pytest.raises(StaleReplay):
        gateway.run(request({"a": "2"}))


def test_replay_reports_a_missing_result(tmp_path: Path) -> None:
    with pytest.raises(ReplayMiss):
        ReplayGateway(tmp_path).run(request({}))
