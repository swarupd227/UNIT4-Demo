from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import get_engine
from app.main import app
from qe.engines import audit

client = TestClient(app)


def test_healthz() -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_people_cover_the_three_roles() -> None:
    roles = {person["role"] for person in client.get("/api/people").json()}
    assert roles == {"qe_lead", "engineer", "full_circuit_owner"}


def test_area_card_counts_the_estate() -> None:
    card = client.get("/api/area").json()
    assert card["rules"] == 20
    assert card["critical_rules"] == 12
    assert card["automated_tests"] == 12
    assert card["gate_percent"] == 80
    assert card["code_lines"] > 3000


def test_audit_chain_detects_a_change() -> None:
    with get_engine().begin() as db:
        audit.record(db, datetime.now(UTC), "Ravi Menon", "engineer", "test_event", "T-1", {"note": "check"})
        assert audit.verify_chain(db)
        db.execute(text("UPDATE qe.audit_event SET detail = '{\"note\": \"changed\"}' WHERE item_id = 'T-1'"))
        assert not audit.verify_chain(db)
        db.rollback()
