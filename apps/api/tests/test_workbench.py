"""Read models, the sign-off gate and the scorecard, against the seeded database."""

import io
import json
import zipfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

CONSULTANT = {"X-Studio-Persona": "consultant"}
CUSTOMER = {"X-Studio-Persona": "customer"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/demo/reset")
        yield test_client
        test_client.post("/api/demo/reset")


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
    assert client.post(f"/api/demo/prepare/{scene}").status_code == 200
    state = client.get("/api/signoff").json()
    assert len(state["open_questions"]) == questions
    assert (client.get("/api/reconciliation/latest").json() is not None) == reconciled
    assert bool(state["pack"] and state["pack"]["signed_at"]) == signed
    assert client.get("/api/audit/verify").json() == {"intact": True}


def test_prepare_rejects_an_unknown_scene(client: TestClient) -> None:
    assert client.post("/api/demo/prepare/9").status_code == 404
