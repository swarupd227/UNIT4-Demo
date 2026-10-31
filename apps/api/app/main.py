from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Connection, text

from app.config import get_settings
from app.db import get_connection
from app.decisions import router as decisions_router
from app.validation import router as validation_router

app = FastAPI(title="Migration Studio API")
app.include_router(decisions_router)
app.include_router(validation_router)

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


class CaseSummary(BaseModel):
    case_id: str
    label: str
    status: str
    customer_name: str
    synthetic: bool
    entity_label: str
    progress: Progress
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
            SELECT c.case_id, c.label, c.status, k.customer_id, k.name AS customer_name, k.synthetic
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
    return CaseSummary(
        entity_label="UK entity",
        progress=Progress(**progress),
        case_id=row["case_id"],
        label=row["label"],
        status=row["status"],
        customer_name=row["customer_name"],
        synthetic=row["synthetic"],
        entities=[LegalEntity(**e) for e in entities],
        estate=[EstateCount(**e) for e in estate],
    )
