from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Connection, text

from app.config import get_settings
from app.db import get_connection
from app.decisions import router as decisions_router
from app.validation import router as validation_router
from app.workbench import router as workbench_router

app = FastAPI(title="Migration Studio API")
app.include_router(decisions_router)
app.include_router(validation_router)
app.include_router(workbench_router)

Db = Annotated[Connection, Depends(get_connection)]


class EstateCount(BaseModel):
    item_type: str
    count: int
    j2x_explained: int


class LegalEntity(BaseModel):
    entity_code: str
    name: str
    status: str
    in_migration_scope: bool


class Progress(BaseModel):
    total: int
    agreed: int
    open_questions: int


class ReconciliationStatus(BaseModel):
    passed: int
    total: int
    exceptions: int


class CaseSummary(BaseModel):
    case_id: str
    label: str
    status: str
    customer_name: str
    synthetic: bool
    entity_label: str
    sector: str
    staff_count: int
    erp_since: int
    cr_since: int
    modules_in_scope: str
    out_of_scope: str
    goal: str
    progress: Progress
    reconciliation: ReconciliationStatus | None
    entities: list[LegalEntity]
    estate: list[EstateCount]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db: Db) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "llm_mode": get_settings().llm_mode}


@app.get("/api/case", response_model=CaseSummary)
def get_case(db: Db) -> CaseSummary:
    row = (
        db.execute(
            text("""
            SELECT c.case_id, c.label, c.status, k.customer_id, k.name AS customer_name, k.synthetic,
                   k.sector, k.staff_count, k.erp_since, k.cr_since, k.modules_in_scope, k.out_of_scope,
                   k.goal
            FROM studio.migration_case c
            JOIN studio.customer k USING (customer_id)
            ORDER BY c.case_id
            LIMIT 1
        """)
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No migration case loaded. Run the seed first.")

    entities = db.execute(
        text("""
            SELECT entity_code, name, status, in_migration_scope
            FROM studio.legal_entity
            WHERE customer_id = :customer_id
            ORDER BY entity_code
        """),
        {"customer_id": row["customer_id"]},
    ).mappings()
    estate = db.execute(
        text("""
            SELECT item_type, count(*) AS count, count(*) FILTER (WHERE j2x_explained) AS j2x_explained
            FROM studio.estate_item
            WHERE case_id = :case_id
            GROUP BY item_type
            ORDER BY item_type
        """),
        {"case_id": row["case_id"]},
    ).mappings()
    progress = (
        db.execute(
            text("""
            SELECT count(*) AS total, count(*) FILTER (WHERE status = 'agreed') AS agreed,
                   (SELECT count(*) FROM studio.customer_question WHERE status = 'open') AS open_questions
            FROM studio.decision
        """)
        )
        .mappings()
        .one()
    )
    reconciliation = (
        db.execute(
            text("""
            SELECT count(*) FILTER (WHERE status = 'pass') AS passed, count(*) AS total,
                   (SELECT count(*) FROM studio.exception e WHERE e.run_id = r.run_id) AS exceptions
            FROM studio.check_result r
            WHERE r.run_id = (SELECT max(run_id) FROM studio.check_run)
            GROUP BY r.run_id
        """)
        )
        .mappings()
        .first()
    )
    return CaseSummary(
        entity_label="UK entity",
        sector=row["sector"],
        staff_count=row["staff_count"],
        erp_since=row["erp_since"],
        cr_since=row["cr_since"],
        modules_in_scope=row["modules_in_scope"],
        out_of_scope=row["out_of_scope"],
        goal=row["goal"],
        reconciliation=ReconciliationStatus(**reconciliation) if reconciliation else None,
        progress=Progress(**progress),
        case_id=row["case_id"],
        label=row["label"],
        status=row["status"],
        customer_name=row["customer_name"],
        synthetic=row["synthetic"],
        entities=[LegalEntity(**e) for e in entities],
        estate=[EstateCount(**e) for e in estate],
    )
