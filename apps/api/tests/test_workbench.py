"""Read models, the sign-off gate and the scorecard, against the seeded database."""

import io
import json
import zipfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from weasyprint import HTML

from app.main import app
from engines.decision.memory import next_proposal
from engines.signoff.pack import workflow_pack_html

CONSULTANT = {"X-Studio-Persona": "consultant"}
CUSTOMER = {"X-Studio-Persona": "customer"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/workspace/reset")
        yield test_client
        test_client.post("/api/workspace/reset")


def clear_questions(client: TestClient) -> None:
    client.post("/api/decisions/CC-014/ask", headers=CONSULTANT, json={"question": "Which threshold?"})
    for question in client.get("/api/signoff").json()["open_questions"]:
        answer = "15%" if question["item_id"] == "CC-014" else "Agreed"
        client.post(f"/api/decisions/{question['item_id']}/answer", headers=CUSTOMER, json={"answer": answer})


def ready_pack(client: TestClient) -> dict:
    clear_questions(client)
    client.post("/api/reconciliation/run")
    response = client.post("/api/signoff/generate", headers=CONSULTANT)
    assert response.status_code == 200, response.text
    return response.json()


def test_case_carries_the_customer_card_and_no_reconciliation_yet(client: TestClient) -> None:
    case = client.get("/api/case").json()
    assert case["staff_count"] == 1800
    assert case["reconciliation"] is None


def test_estate_totals(client: TestClient) -> None:
    estate = client.get("/api/estate").json()
    assert {t["item_type"]: t["count"] for t in estate["types"]}["RP"] == 148
    assert len(estate["integrations"]) == 14
    assert estate["j2x"]["simulated"] is True


def test_report_overview_matches_the_plan(client: TestClient) -> None:
    overview = client.get("/api/reports/overview").json()
    counts = (overview["retire"], overview["merged"], overview["standard"], overview["rebuild"])
    assert counts == (60, 38, 31, 17)
    assert overview["merged_into"] == 9
    assert [r["item_id"] for r in overview["held"]] == ["RP-058", "RP-112"]
    assert sum(counts) + len(overview["held"]) == overview["total"] == 148


def test_parity_endpoint_returns_both_steps(client: TestClient) -> None:
    report = client.post("/api/reports/RP-077/parity").json()
    assert report["cr_total"] == report["faithful_rebuild_total"]
    assert client.post("/api/reports/RP-001/parity").status_code == 404


def test_workflows_rank_by_usage_with_the_pack(client: TestClient) -> None:
    data = client.get("/api/workflows").json()
    assert len(data["variants"]) == 9
    assert data["variants"][0]["item_id"] == "WF-002"
    assert data["pack"]["to_count"] == 3


def test_gate_blocks_generation_until_conditions_are_met(client: TestClient) -> None:
    state = client.get("/api/signoff").json()
    assert not state["ready_to_generate"]
    assert client.post("/api/signoff/generate", headers=CONSULTANT).status_code == 409


def test_a_new_answer_makes_reconciliation_out_of_date(client: TestClient) -> None:
    clear_questions(client)
    client.post("/api/reconciliation/run")
    assert client.get("/api/signoff").json()["ready_to_generate"]
    client.post("/api/decisions/CC-014/ask", headers=CONSULTANT, json={"question": "Change it?"})
    client.post("/api/decisions/CC-014/answer", headers=CUSTOMER, json={"answer": "10%"})
    state = client.get("/api/signoff").json()
    assert not next(c for c in state["conditions"] if c["key"] == "reconciliation")["passed"]


def test_pack_contains_verifiable_evidence(client: TestClient) -> None:
    state = ready_pack(client)
    pack_id = state["pack"]["pack_id"]
    pdf = client.get(f"/api/signoff/{pack_id}/signoff_pack.pdf")
    assert pdf.content.startswith(b"%PDF")
    archive = client.get(f"/api/signoff/{pack_id}/signoff_pack.zip")
    with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert "not cutover" in manifest["scope"]
        import hashlib

        for name, expected in manifest["files"].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected


def test_only_the_customer_signs_and_only_a_current_pack(client: TestClient) -> None:
    ready_pack(client)
    assert client.post("/api/signoff/sign", headers=CONSULTANT).status_code == 403
    client.post("/api/decisions/CC-041/accept", headers=CONSULTANT)
    assert client.post("/api/signoff/sign", headers=CUSTOMER).status_code == 409
    client.post("/api/signoff/generate", headers=CONSULTANT)
    state = client.post("/api/signoff/sign", headers=CUSTOMER).json()
    assert state["pack"]["signed_by"] == "Jordan Ashby"
    assert client.post("/api/signoff/sign", headers=CUSTOMER).status_code == 409


def test_file_download_rejects_other_names(client: TestClient) -> None:
    assert client.get("/api/signoff/1/secrets.txt").status_code == 404


def test_scorecard_is_computed_and_quotes_no_saving(client: TestClient) -> None:
    client.post("/api/timing", headers=CONSULTANT, json={"stage": "decisions", "seconds": 120})
    client.post("/api/reconciliation/run")
    card = client.get("/api/scorecard").json()
    assert (card["found"], card["planted"]) == (10, 10)
    assert card["stages"][0] == {"stage": "Decision", "seconds": 120, "consultant_seconds": 120}
    assert card["reconciliation"]["passed"] == 4
    assert card["artefacts"][0]["source"] == "hand_authored"
    assert "saving" not in json.dumps(card).lower()


def test_defects_read_the_first_real_run(client: TestClient) -> None:
    clear_questions(client)
    client.post("/api/reconciliation/run")
    assert client.get("/api/scorecard").json()["defects"] == {"tested": 2, "failed": 0}


def test_routine_decisions_start_agreed_and_are_labelled(client: TestClient) -> None:
    rows = client.get("/api/decisions").json()
    agreed = [row for row in rows if row["status"] == "agreed"]
    assert len(agreed) > 50
    seeded = [row for row in agreed if row["item_id"] != "RP-031"]
    assert not {row["outcome"] for row in seeded} & {"retire", "rebuild_extension", "product_gap"}
    assert not any(row["flags"] or row["item_type"] == "CF" or row["confidence"] < 85 for row in seeded)
    trail = client.get(f"/api/decisions/{seeded[0]['item_id']}").json()["audit"]
    assert trail[0]["action"] == "accepted_seeded"
    assert client.get("/api/audit/verify").json() == {"intact": True}


def test_hero_items_stay_open(client: TestClient) -> None:
    rows = {row["item_id"]: row["status"] for row in client.get("/api/decisions").json()}
    for item_id in ("CC-014", "RP-077", "RP-084", "RP-112", "WF-006", "CF-203", "CF-204", "CC-037", "CC-018"):
        assert rows[item_id] != "agreed", item_id


def test_pack_states_how_much_is_seeded(client: TestClient) -> None:
    summary = ready_pack(client)["pack"]["summary"]
    assert 0 < summary["seeded_history"] < summary["agreed"]


@pytest.mark.parametrize(
    ("scene", "questions", "reconciled", "signed"),
    [(0, 4, False, False), (6, 4, False, False), (7, 0, True, False), (8, 0, True, True)],
)
def test_prepare_rebuilds_the_state_each_scene_expects(
    client: TestClient, scene: int, questions: int, reconciled: bool, signed: bool
) -> None:
    assert client.post(f"/api/workspace/prepare/{scene}").status_code == 200
    state = client.get("/api/signoff").json()
    assert len(state["open_questions"]) == questions
    assert (client.get("/api/reconciliation/latest").json() is not None) == reconciled
    assert bool(state["pack"] and state["pack"]["signed_at"]) == signed
    assert client.get("/api/audit/verify").json() == {"intact": True}


def test_prepare_rejects_an_unknown_scene(client: TestClient) -> None:
    assert client.post("/api/workspace/prepare/9").status_code == 404


def run_with_duplicate_value(client: TestClient) -> dict:
    run = client.post("/api/reconciliation/run").json()
    return next(e for e in run["exceptions"] if e["code"] == "duplicate_dimension_value")


def test_only_the_named_approver_can_approve_an_exception(client: TestClient) -> None:
    exception = run_with_duplicate_value(client)
    url = f"/api/reconciliation/exceptions/{exception['exception_id']}/approve"
    assert client.post(url, headers=CUSTOMER).status_code == 403
    assert client.post(url, headers=CONSULTANT).status_code == 200
    assert client.post(url, headers=CONSULTANT).status_code == 409
    assert (
        client.post("/api/reconciliation/exceptions/EX-R9-1/approve", headers=CONSULTANT).status_code == 404
    )


def test_an_approval_survives_a_rerun_without_changing_the_result(client: TestClient) -> None:
    exception = run_with_duplicate_value(client)
    before = client.get("/api/reconciliation/latest").json()["result_hash"]
    client.post(f"/api/reconciliation/exceptions/{exception['exception_id']}/approve", headers=CONSULTANT)
    rerun = client.post("/api/reconciliation/run").json()
    assert rerun["result_hash"] == before
    approved = next(e for e in rerun["exceptions"] if e["code"] == "duplicate_dimension_value")
    assert approved["approved_by"] == "Robin Hale"
    assert next(c for c in rerun["checks"] if c["check_id"] == "R6")["status"] == "fail"


def test_a_reset_clears_exception_approvals(client: TestClient) -> None:
    exception = run_with_duplicate_value(client)
    client.post(f"/api/reconciliation/exceptions/{exception['exception_id']}/approve", headers=CONSULTANT)
    client.post("/api/workspace/reset")
    assert run_with_duplicate_value(client)["approved_by"] is None


def test_the_pack_records_who_approved_an_exception(client: TestClient) -> None:
    exception = run_with_duplicate_value(client)
    client.post(f"/api/reconciliation/exceptions/{exception['exception_id']}/approve", headers=CONSULTANT)
    pack = ready_pack(client)["pack"]
    archive = client.get(f"/api/signoff/{pack['pack_id']}/signoff_pack.zip").content
    log = zipfile.ZipFile(io.BytesIO(archive)).read("exception_log.csv").decode()
    assert "Robin Hale" in log


def test_consultant_effort_is_reported_per_case(client: TestClient) -> None:
    client.post("/api/timing", headers=CONSULTANT, json={"stage": "reports", "seconds": 30})
    client.post("/api/timing", headers=CUSTOMER, json={"stage": "reports", "seconds": 15})
    cases = {row["case"]: row["consultant_seconds"] for row in client.get("/api/scorecard").json()["cases"]}
    assert cases == {"Case 1: custom code": 0, "Case 2: report estate": 30, "Case 3: approval workflows": 0}


def test_the_workflow_decision_pack_is_one_page(client: TestClient) -> None:
    pack = client.get("/api/workflows").json()["pack"]
    response = client.get("/api/workflows/decision-pack.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    usage = {workflow["keeps"]: 1000 for workflow in pack["proposed"]}
    assert len(HTML(string=workflow_pack_html("Ardleigh Consulting Group", pack, usage)).render().pages) == 1


def test_memory_offers_the_most_approved_outcome() -> None:
    history = [("retire", "approved"), ("retire", "approved"), ("keep_repoint", "approved")]
    assert next_proposal(history) == ("retire", 80)


def test_memory_stops_offering_a_rejected_outcome() -> None:
    assert next_proposal([("retire", "approved"), ("retire", "rejected")]) == (None, None)


def test_memory_confidence_has_a_ceiling() -> None:
    assert next_proposal([("retire", "approved")] * 20) == ("retire", 95)


def test_an_edit_reaches_mapping_memory_on_the_scorecard(client: TestClient) -> None:
    assert client.get("/api/scorecard").json()["memory"]["entries"] == []
    row = next(r for r in client.get("/api/decisions").json() if r["status"] == "review" and r["outcome"])
    edited = "keep_repoint" if row["outcome"] != "keep_repoint" else "retire"
    response = client.post(
        f"/api/decisions/{row['item_id']}/edit",
        headers=CONSULTANT,
        json={"outcome": edited, "reason": "Still needed"},
    )
    assert response.status_code == 200, response.text
    memory = client.get("/api/scorecard").json()["memory"]
    assert memory["rejected"] == 1
    assert memory["entries"][0]["item_id"] == row["item_id"]
    assert memory["entries"][0]["next_outcome"] != row["outcome"]
