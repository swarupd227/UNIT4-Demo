import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from app.config import get_settings
from app.db import Db
from qe.engines.estate import estate


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Read the estate while the API starts, so the first screen does not wait for the file reads.
    threading.Thread(target=_area_card, daemon=True).start()
    yield


app = FastAPI(title="Test Assurance API", lifespan=lifespan)


class Person(BaseModel):
    person_key: str
    name: str
    role: str
    org: str


class AreaCard(BaseModel):
    area: str
    module: str
    rules: int
    critical_rules: int
    manual_cases: int
    automated_tests: int
    defects: int
    code_files: int
    code_lines: int
    help_pages: int
    gate_percent: int


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db: Db) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "llm_mode": get_settings().llm_mode}


@app.get("/api/people", response_model=list[Person])
def people(db: Db) -> list[Person]:
    rows = db.execute(
        text("SELECT person_key, name, role, org FROM qe.person ORDER BY person_key")
    ).mappings()
    return [Person(**row) for row in rows]


@app.get("/api/area", response_model=AreaCard)
def area() -> AreaCard:
    return _area_card()


# The estate is read from files on a mounted volume, which is slow, and it does not change while the
# API runs. The API reloads when its code changes, which also clears this.
@lru_cache(maxsize=1)
def _area_card() -> AreaCard:
    settings = get_settings()
    source = estate(settings.estate_root)
    rules = source.rules()
    return AreaCard(
        area="Project billing",
        module="Project Billing 4.8",
        rules=len(rules),
        critical_rules=sum(1 for rule in rules if rule["critical"]),
        manual_cases=len(source.manual_cases()),
        automated_tests=source.automated_tests(),
        defects=len(source.defects()),
        code_files=len(source.code_files()),
        code_lines=source.code_lines(),
        help_pages=source.help_pages(),
        gate_percent=settings.gate_percent,
    )
