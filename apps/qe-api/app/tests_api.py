"""Generated tests: the intake of the batch, every attempt at every test, and the proof of each."""

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.context import analysis
from qe.engines import generation

router = APIRouter(prefix="/api")

LIVE_TIMEOUT_SECONDS = 120
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


@router.post("/tests/{test_id}/live")
def live_check(test_id: str) -> dict[str, Any]:
    """Runs one accepted test now against the build that puts its fault back. It should fail."""
    entries = generation.history().get(test_id)
    if not entries or not entries[-1]["accepted"]:
        raise HTTPException(404, "No accepted test with that id.")
    test = entries[-1]
    faults = test["checks"]["faults"]
    fault_id = (faults.get("required") or faults["caught"])[0]
    fault = next(f for f in _faults() if f["id"] == fault_id)
    request = urllib.request.Request(
        f"{get_settings().lab_url}/run",
        data=json.dumps(
            {
                "build": fault_id,
                "grep": re.escape(test["title"]),
                "overlay": f"/estate/generated/attempt-{test['attempt']}",
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=LIVE_TIMEOUT_SECONDS) as response:
            run = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise HTTPException(
            error.code, json.loads(error.read()).get("error", "The lab refused the check.")
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise HTTPException(503, "The lab could not be reached. Show the recorded result instead.") from error
    result = next((t for t in run.get("tests", []) if t["title"] == test["title"]), None)
    if result is None:
        raise HTTPException(502, "The lab ran, but the test did not report a result.")
    return {
        "test": test["title"],
        "build": fault_id,
        "fault": fault["description"],
        "status": result["status"],
        "caught": result["status"] == "failed",
        "error": (result["error"] or "").split("\n")[0],
        "seconds": round(time.monotonic() - started, 1),
    }


def _faults() -> list[dict[str, Any]]:
    return yaml.safe_load((generation.QE_ROOT / "faults" / "faults.yaml").read_text(encoding="utf-8"))[
        "faults"
    ]
