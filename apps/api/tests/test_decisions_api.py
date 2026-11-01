"""Contract tests against the seeded database. Each test starts from the demo's start state."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app

CONSULTANT = {"X-Studio-Persona": "consultant"}
CUSTOMER = {"X-Studio-Persona": "customer"}
TECHNICAL = {"X-Studio-Persona": "unit4_technical"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        test_client.post("/api/workspace/reset")
        yield test_client
        test_client.post("/api/workspace/reset")


def status(client: TestClient, item_id: str) -> str:
    return client.get(f"/api/decisions/{item_id}").json()["status"]


def first_retire(client: TestClient) -> str:
    rows = client.get("/api/decisions").json()
    return next(r["item_id"] for r in rows if r["outcome"] == "retire" and r["status"] == "review")


def test_start_state_matches_the_mock_up(client: TestClient) -> None:
    expected = {
        "CC-014": ("rebuild_extension", "review"),
        "RP-077": ("keep_repoint", "review"),
        "RP-112": (None, "question"),
        "RP-031": ("retire", "agreed"),
        "WF-006": ("retire", "question"),
        "CF-203": ("replace_standard", "conflict"),
    }
    for item_id, values in expected.items():
        row = client.get(f"/api/decisions/{item_id}").json()
        assert (row["outcome"], row["status"]) == values


def test_hidden_dependency_is_shown(client: TestClient) -> None:
    labels = [e["label"] for e in client.get("/api/decisions/CC-014").json()["evidence"]]
    assert "INT-09 also writes zz_rate_override" in labels


def test_code_evidence_points_at_the_threshold_line(client: TestClient) -> None:
    item = client.get("/api/decisions/CC-014").json()
    line = next(e["line"] for e in item["evidence"] if e["label"].startswith("Threshold"))
    assert "0.10m" in item["source_text"].splitlines()[line - 1]


def test_an_agent_role_is_rejected(client: TestClient) -> None:
    response = client.post("/api/decisions/CC-014/accept", headers={"X-Studio-Persona": "agent"})
    assert response.status_code == 422


def test_retirement_needs_consultant_then_customer(client: TestClient) -> None:
    item_id = first_retire(client)
    assert client.post(f"/api/decisions/{item_id}/accept", headers=CUSTOMER).status_code == 403
    assert client.post(f"/api/decisions/{item_id}/accept", headers=CONSULTANT).status_code == 200
    assert status(client, item_id) == "awaiting"
    assert client.post(f"/api/decisions/{item_id}/accept", headers=CUSTOMER).status_code == 200
    assert status(client, item_id) == "agreed"


def test_extension_needs_the_unit4_technical_lead(client: TestClient) -> None:
    client.post("/api/decisions/CC-014/accept", headers=CONSULTANT)
    assert status(client, "CC-014") == "awaiting"
    assert client.post("/api/decisions/CC-014/accept", headers=TECHNICAL).status_code == 200
    assert status(client, "CC-014") == "agreed"


def test_held_item_cannot_be_accepted(client: TestClient) -> None:
    assert client.post("/api/decisions/RP-112/accept", headers=CONSULTANT).status_code == 403


def test_conflict_blocks_acceptance_until_answered(client: TestClient) -> None:
    assert client.post("/api/decisions/CF-203/accept", headers=CONSULTANT).status_code == 403
    client.post("/api/decisions/CF-203/ask", headers=CONSULTANT, json={"question": "Keep two accounts?"})
    assert status(client, "CF-203") == "question"
    assert (
        client.post("/api/decisions/CF-203/answer", headers=CONSULTANT, json={"answer": "x"}).status_code
        == 403
    )
    client.post("/api/decisions/CF-203/answer", headers=CUSTOMER, json={"answer": "Keep two ERPx accounts"})
    assert status(client, "CF-203") == "review"
    assert client.post("/api/decisions/CF-203/accept", headers=CONSULTANT).status_code == 200


def test_edit_clears_approvals_and_is_consultant_only(client: TestClient) -> None:
    item_id = first_retire(client)
    client.post(f"/api/decisions/{item_id}/accept", headers=CONSULTANT)
    body = {"outcome": "keep_repoint", "reason": "Finance still needs this"}
    assert client.post(f"/api/decisions/{item_id}/edit", headers=CUSTOMER, json=body).status_code == 403
    assert client.post(f"/api/decisions/{item_id}/edit", headers=CONSULTANT, json=body).status_code == 200
    item = client.get(f"/api/decisions/{item_id}").json()
    assert (item["outcome"], item["status"], item["approvals"]) == ("keep_repoint", "review", [])
    assert item["reason"]  # the original proposal is preserved


def test_bulk_accept_skips_what_the_role_cannot_accept(client: TestClient) -> None:
    item_id = first_retire(client)
    body = {"item_ids": [item_id, "RP-112", "RP-031"]}
    result = client.post("/api/decisions/bulk-accept", headers=CONSULTANT, json=body).json()
    assert result == {"accepted": 1, "skipped": 2}


def test_audit_chain_detects_nothing_after_normal_use(client: TestClient) -> None:
    client.post("/api/decisions/CC-014/accept", headers=CONSULTANT)
    assert client.get("/api/audit/verify").json() == {"intact": True}
    trail = client.get("/api/decisions/CC-014").json()["audit"]
    assert [e["action"] for e in trail] == ["accepted", "proposed"]
