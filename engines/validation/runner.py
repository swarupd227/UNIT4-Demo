"""Runs the versioned checks. No language model is involved: the same input gives the same result."""

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import Connection, text

from engines.validation import checks
from engines.validation.causes import explain

DEFINITIONS = Path(__file__).parent / "definitions"
HANDLERS: dict[str, Callable[[Connection], dict[str, Any]]] = {
    "report_parity": checks.report_parity,
    "billing_rule_tests": checks.billing_rule_tests,
}
INPUT_TABLES = [
    "cr_source.account", "cr_source.account_map", "cr_source.ap_open_item", "cr_source.ar_open_item",
    "cr_source.customer", "cr_source.dimension_map", "cr_source.dimension_value", "cr_source.fx_rate",
    "cr_source.gl_balance", "cr_source.project", "cr_source.resource_reference", "cr_source.supplier",
    "cr_source.utilisation_summary", "cr_source.wip_item", "erpx_sim.account", "erpx_sim.ap_open_item",
    "erpx_sim.ar_open_item", "erpx_sim.customer", "erpx_sim.dimension_value", "erpx_sim.fx_rate",
    "erpx_sim.gl_balance", "erpx_sim.project", "erpx_sim.supplier", "erpx_sim.utilisation_summary",
    "erpx_sim.wip_item",
]  # fmt: skip


def load_definitions() -> list[dict[str, Any]]:
    return [yaml.safe_load(path.read_text(encoding="utf-8")) for path in sorted(DEFINITIONS.glob("R*.yaml"))]


def definitions_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(DEFINITIONS.glob("R*.yaml")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def current_input_hash(db: Connection) -> str:
    digest = hashlib.sha256()
    for table in INPUT_TABLES:
        value = db.execute(
            text(
                f"SELECT coalesce(md5(string_agg(md5(t::text), '' ORDER BY md5(t::text))), '') FROM {table} t"
            )
        ).scalar_one()
        digest.update(f"{table}={value}\n".encode())
    digest.update(f"threshold={checks.chosen_threshold(db)}\n".encode())
    return digest.hexdigest()


def _run_sql(db: Connection, definition: dict[str, Any]) -> dict[str, Any]:
    totals = db.execute(text(definition["totals"])).mappings().one()
    differences = [dict(row) for row in db.execute(text(definition["differences"])).mappings()]
    return {
        **{key: int(value) for key, value in totals.items()},
        "status": "fail" if differences else "pass",
        "differences": differences,
        "summary": {},
    }


def _run_check(db: Connection, definition: dict[str, Any]) -> dict[str, Any]:
    if definition["type"] == "sql":
        return _run_sql(db, definition)
    return HANDLERS[definition["handler"]](db)


def _json_default(value: Any) -> str:
    return str(value)


def run_checks(db: Connection) -> int:
    started = datetime.now(UTC)
    input_hash = current_input_hash(db)
    results = []
    for definition in load_definitions():
        result = _run_check(db, definition)
        exceptions = explain(db, definition["id"], result["differences"])
        results.append({"definition": definition, "result": result, "exceptions": exceptions})

    canonical = json.dumps(
        [
            {"check": r["definition"]["id"], "result": r["result"], "exceptions": r["exceptions"]}
            for r in results
        ],
        sort_keys=True,
        default=_json_default,
    )
    run_id = db.execute(
        text("""
            INSERT INTO studio.check_run (started_at, finished_at, definitions_hash, input_hash, result_hash)
            VALUES (:started, :finished, :definitions_hash, :input_hash, :result_hash)
            RETURNING run_id
        """),
        {
            "started": started,
            "finished": datetime.now(UTC),
            "definitions_hash": definitions_hash(),
            "input_hash": input_hash,
            "result_hash": hashlib.sha256(canonical.encode()).hexdigest(),
        },
    ).scalar_one()

    for entry in results:
        _store(db, run_id, entry["definition"], entry["result"], entry["exceptions"])
    return run_id


def _store(
    db: Connection,
    run_id: int,
    definition: dict[str, Any],
    result: dict[str, Any],
    exceptions: list[dict[str, Any]],
) -> None:
    check_id = definition["id"]
    db.execute(
        text("""
            INSERT INTO studio.check_result
                (run_id, check_id, version, name, compares, tolerance, status, unit, source_value,
                 target_value, source_count, target_count, difference_count, summary)
            VALUES (:run_id, :check_id, :version, :name, :compares, :tolerance, :status, :unit, :source_value,
                    :target_value, :source_count, :target_count, :difference_count, CAST(:summary AS jsonb))
        """),
        {
            "run_id": run_id,
            "check_id": check_id,
            "version": definition["version"],
            "name": definition["name"],
            "compares": definition["compares"],
            "tolerance": definition["tolerance"],
            "unit": definition["unit"],
            "status": result["status"],
            "source_value": result["source_value"],
            "target_value": result["target_value"],
            "source_count": result["source_count"],
            "target_count": result["target_count"],
            "difference_count": len(result["differences"]),
            "summary": json.dumps(result["summary"], default=_json_default),
        },
    )
    if result["differences"]:
        db.execute(
            text("""
                INSERT INTO studio.check_difference
                    (run_id, check_id, row_number, row_key, source_value, target_value, difference, detail)
                VALUES (:run_id, :check_id, :row_number, :row_key, :source_value, :target_value, :difference,
                        CAST(:detail AS jsonb))
            """),
            [
                {
                    **row,
                    "run_id": run_id,
                    "check_id": check_id,
                    "row_number": number,
                    "detail": json.dumps(row["detail"], default=_json_default),
                }
                for number, row in enumerate(result["differences"], start=1)
            ],
        )
    for number, exception in enumerate(exceptions, start=1):
        db.execute(
            text("""
                INSERT INTO studio.exception
                    (run_id, exception_id, check_id, code, title, cause, proposed_action, approver_role,
                     amount_minor, detail, status)
                VALUES (:run_id, :exception_id, :check_id, :code, :title, :cause, :proposed_action,
                        :approver_role, :amount_minor, CAST(:detail AS jsonb), 'open')
            """),
            {
                **exception,
                "run_id": run_id,
                "check_id": check_id,
                "exception_id": f"EX-{check_id}-{number}",
                "detail": json.dumps(exception["detail"], default=_json_default),
            },
        )
