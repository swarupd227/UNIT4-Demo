from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import get_engine
from app.main import app

client = TestClient(app)


def _flaky() -> dict[str, Any]:
    response = client.get("/api/flaky")
    assert response.status_code == 200
    return response.json()


def test_both_flaky_tests_are_diagnosed_with_their_real_cause() -> None:
    causes = {t["test"]["rule"]: t["diagnosis"]["cause"] for t in _flaky()["tests"]}
    assert causes == {"BR-01": "shared_data", "BR-09": "fixed_wait"}


def test_flaky_rates_are_measured_before_the_fix() -> None:
    for entry in _flaky()["tests"]:
        assert 2 <= entry["test"]["failed"] <= 14 and entry["test"]["runs"] == 20


def test_t7_evidence_shows_the_discount_test_running_alongside_every_failure() -> None:
    br01 = next(t for t in _flaky()["tests"] if t["test"]["rule"] == "BR-01")["test"]
    discount = next(o for o in br01["running_alongside"] if o["test"].startswith("BR-16"))
    assert discount["when_failed"] == discount["failed_runs"]
    assert any(s["changes"] for s in br01["shared_data"])


def test_both_flaky_tests_pass_20_of_20_after_their_fixes() -> None:
    data = _flaky()
    assert data["runs_after"] == 20
    for entry in data["tests"]:
        assert entry["after"] == {"failed": 0, "runs": 20}
    assert data["failures_after"] == 0


def test_fixes_remove_the_cause_without_retries_or_waits() -> None:
    fixes = {t["test"]["rule"]: t["diagnosis"]["files"] for t in _flaky()["tests"]}
    numbering = next(f for f in fixes["BR-09"] if f["path"].endswith("numbering.spec.ts"))
    assert "waitForTimeout" not in numbering["content"]
    discount = next(f for f in fixes["BR-01"] if f["path"].endswith("discount.spec.ts"))
    assert "customers.halden" not in discount["content"]


def test_selector_repair_is_measured_and_the_suite_passes_on_the_new_release() -> None:
    data = client.get("/api/maintenance").json()
    assert data["failures"], "the release should break at least one test"
    assert all(f["path"].startswith("pages/") for f in data["repair"]["files"])
    assert data["after"]["failed"] == 0 and data["after"]["tests"] >= 22
    timing = data["timing"]
    assert timing["detect_seconds"] > 0 and timing["verify_seconds"] > 0 and timing["repair_seconds"] > 0


@pytest.fixture
def clean_review() -> Any:
    started = datetime.now(UTC)
    yield "REPAIR-release-4.9"
    with get_engine().begin() as db:
        db.execute(text("DELETE FROM qe.change_review WHERE change_id = 'REPAIR-release-4.9'"))
        db.execute(
            text("DELETE FROM qe.audit_event WHERE item_id = 'REPAIR-release-4.9' AND at >= :at"),
            {"at": started},
        )


def test_only_an_engineer_approves_a_change_to_tests(clean_review: str) -> None:
    url = f"/api/changes/{clean_review}/review"
    assert (
        client.post(url, json={"person_key": "full_circuit_owner", "decision": "approved"}).status_code == 403
    )
    assert client.post(url, json={"person_key": "engineer", "decision": "approved"}).status_code == 200
    assert client.post(url, json={"person_key": "engineer", "decision": "approved"}).status_code == 409
    assert client.get("/api/maintenance").json()["review"]["reviewed_by"] == "Ravi Menon"
