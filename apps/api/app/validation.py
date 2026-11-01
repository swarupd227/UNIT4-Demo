from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import Connection, text

from app.decisions import Tx
from engines.scoring.score import score
from engines.validation.runner import run_checks

router = APIRouter(prefix="/api")


def _latest_run_id(db: Connection) -> int | None:
    return db.execute(text("SELECT max(run_id) FROM studio.check_run")).scalar()


def _run_report(db: Connection, run_id: int) -> dict[str, Any]:
    params = {"run_id": run_id}
    run = db.execute(text("SELECT * FROM studio.check_run WHERE run_id = :run_id"), params).mappings().one()
    checks = db.execute(
        text("SELECT * FROM studio.check_result WHERE run_id = :run_id ORDER BY check_id"), params
    ).mappings()
    exceptions = db.execute(
        text("SELECT * FROM studio.exception WHERE run_id = :run_id ORDER BY exception_id"), params
    ).mappings()
    return {**run, "checks": [dict(c) for c in checks], "exceptions": [dict(e) for e in exceptions]}


@router.post("/reconciliation/run")
def run_reconciliation(db: Tx) -> dict[str, Any]:
    return _run_report(db, run_checks(db))


@router.get("/reconciliation/latest")
def latest_reconciliation(db: Tx) -> dict[str, Any] | None:
    run_id = _latest_run_id(db)
    return _run_report(db, run_id) if run_id is not None else None


@router.get("/reconciliation/{check_id}/differences")
def check_differences(check_id: str, db: Tx, limit: int = Query(200, le=1000)) -> list[dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT row_number, row_key, source_value, target_value, difference, detail
            FROM studio.check_difference
            WHERE run_id = (SELECT max(run_id) FROM studio.check_run) AND check_id = :check_id
            ORDER BY row_number LIMIT :limit
        """),
        {"check_id": check_id, "limit": limit},
    ).mappings()
    return [dict(row) for row in rows]


@router.get("/artefacts/{item_id}")
def artefacts(item_id: str, db: Tx) -> list[dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT kind, content, source, model, duration_ms, prompt_version
            FROM studio.artefact WHERE item_id = :item_id ORDER BY kind
        """),
        {"item_id": item_id},
    ).mappings()
    return [dict(row) for row in rows]


@router.get("/score")
def get_score(db: Tx) -> dict[str, Any]:
    return score(db)
