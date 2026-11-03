"""Generated tests: the intake of the batch, every attempt at every test, and the proof of each."""

import json
from typing import Any

import yaml
from fastapi import APIRouter

from app.config import get_settings
from app.context import analysis
from qe.engines import generation

router = APIRouter(prefix="/api")

KIND_LABEL = {"manual_case": "Manual case", "defect": "Defect", "hidden_rule": "Hidden rule"}


def _intake() -> list[dict[str, Any]]:
    path = generation.GENERATED / "intake.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


@router.get("/tests")
def tests() -> dict[str, Any]:
    attempts = generation.history()
    latest = [entries[-1] for entries in attempts.values()]
    accepted = [c for c in latest if c["accepted"]]
    result = analysis()
    batch = yaml.safe_load(generation.BATCH.read_text(encoding="utf-8"))
    return {
        "batch": batch,
        "intake": _intake(),
        "tests": [
            {
                "id": entries[-1]["id"],
                "kind": KIND_LABEL[entries[-1]["kind"]],
                "ref": entries[-1]["ref"],
                "rule": entries[-1]["rule"],
                "title": entries[-1]["title"],
                "accepted": entries[-1]["accepted"],
                "attempts": entries,
            }
            for entries in attempts.values()
        ],
        "coverage_before": result["summary"],
        "coverage_after": generation.coverage_after(
            result["coverage"], accepted, get_settings().gate_percent
        ),
    }
