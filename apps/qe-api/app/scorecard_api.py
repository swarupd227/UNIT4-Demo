"""The gap list, the scorecard with the RFP's measures, and the evidence pack.

Every figure is calculated here by plain code from the lab's results, the agents' checked results and
the people's decisions. Manual run times per case are the one assumption: the quality engineering
lead recorded them in the answer key.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter
from sqlalchemy import Connection, text

from app import maintenance_api, review_api, tests_api
from app.config import get_settings
from app.context import analysis
from app.db import Db
from qe.engines import audit

router = APIRouter(prefix="/api")


def _key(name: str) -> dict[str, Any]:
    return yaml.safe_load((Path(get_settings().answer_key) / name).read_text(encoding="utf-8"))


def _approved_context(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        text("SELECT entry_id, kind, title FROM qe.context_entry WHERE status = 'approved' ORDER BY entry_id")
    ).mappings()
    return [dict(row) for row in rows]


def gaps(db: Connection) -> dict[str, Any]:
    result = analysis()
    tests = tests_api.tests()
    after = {r["rule"]: r for r in tests["coverage_after"]["rules"]}
    risk = {r["rule"]: (n, r) for n, r in enumerate(result["risk_ranking"])}
    rows = {r["rule"]: r for r in result["coverage"]}
    caught_new = {
        f for t in tests["tests"] if t["accepted"] for f in t["attempts"][-1]["checks"]["faults"]["caught"]
    }
    below = []
    for rule, row in after.items():
        if row["covered"]:
            continue
        faults = rows[rule]["faults"]
        missed = [f for f in faults if not f["caught"] and f["id"] not in caught_new]
        rank, facts = risk.get(rule, (99, {"defects": [], "untested": 0}))
        below.append(
            {
                "rule": rule,
                "title": row["title"],
                "critical": row["critical"],
                "score": row["score"],
                "tests": row["tests"],
                "missed_faults": [{"id": f["id"], "description": f["description"]} for f in missed],
                "defects": len(facts["defects"]),
                "untested_defects": facts["untested"],
                "manual_cases": rows[rule]["manual_cases"],
                "rank": rank,
            }
        )
    below.sort(key=lambda r: (not r["critical"], r["rank"], r["rule"]))
    waiting = [
        {
            "case": e["case"],
            "title": e["title"],
            "outcome": e["outcome"],
            "review": e.get("review", {}).get("summary"),
        }
        for e in tests["intake"]
        if e["outcome"] in ("to_person", "needs_expected_result")
    ]
    return {
        "gate_percent": get_settings().gate_percent,
        "covered": tests["coverage_after"]["critical_covered"],
        "critical_rules": tests["coverage_after"]["critical_rules"],
        "percent": tests["coverage_after"]["percent"],
        "below_gate": below,
        "waiting_on_people": waiting,
        "dead_code": result["dead_code"],
    }


def _planted(tests: dict[str, Any], flaky: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    intake = {e["case"]: e for e in tests["intake"]}
    by_ref = {t["ref"]: t for t in tests["tests"]}
    accepted = [t for t in tests["tests"] if t["accepted"]]
    caught = {f for t in accepted for f in t["attempts"][-1]["checks"]["faults"]["caught"]}
    causes = {t["test"]["rule"]: t for t in flaky["tests"]}
    br04 = next((r for r in result["risk_ranking"] if r["rule"] == "BR-04"), None)
    hidden = result["hidden_rules"].get("content", {}).get("rules", [])

    def weak_then_fixed(test: dict[str, Any]) -> bool:
        first = test["attempts"][0]["checks"]
        return (
            first["faults"]["ran"] and not first["faults"]["passed"] and first["stability"]["passed"]
        ) and test["accepted"]

    def fixed(rule: str, cause: str) -> bool:
        entry = causes.get(rule)
        return bool(
            entry and entry["diagnosis"]["cause"] == cause and entry["after"] and not entry["after"]["failed"]
        )

    return [
        {
            "id": "T1",
            "what": "Seven rounding defects and no automated test",
            "handled": bool(br04 and len(br04["defects"]) == 7)
            and {"F04a", "F04b", "F04c", "F04d"} <= caught,
            "how": "Risk card: 7 defects in RoundingHelper.cs; the new tests catch all four rounding faults",
        },
        {
            "id": "T2",
            "what": "Write-down approval above 10% in code only",
            "handled": any(not h["documented"] and h["related_rule"] == "BR-07" for h in hidden)
            and {"F07a", "F07b"} <= caught,
            "how": "Hidden rule found in code only; its test catches both approval faults",
        },
        {
            "id": "T3",
            "what": "A generated test that passes but protects nothing",
            "handled": any(weak_then_fixed(t) for t in tests["tests"]),
            "how": "Rejected by the fault check, regenerated, then accepted",
        },
        {
            "id": "T4",
            "what": "Manual case conflicts with the documentation",
            "handled": intake.get("48207", {}).get("outcome") == "to_person" and "MC-48207" not in by_ref,
            "how": "Sent to a person; no test generated",
        },
        {
            "id": "T5",
            "what": "Vague expected result",
            "handled": intake.get("48230", {}).get("outcome") == "needs_expected_result",
            "how": "The validator asked for a concrete expected result",
        },
        {
            "id": "T6",
            "what": "Fixed wait",
            "handled": fixed("BR-09", "fixed_wait"),
            "how": "Wait replaced; 20 of 20",
        },
        {
            "id": "T7",
            "what": "Two tests share and change the same data",
            "handled": fixed("BR-01", "shared_data"),
            "how": "The discount test owns its own customer; 20 of 20",
        },
        {
            "id": "T8",
            "what": "Duplicate manual cases",
            "handled": intake.get("48229", {}).get("outcome") == "merged",
            "how": "Merged; the existing BR-12 test already covers both",
        },
        {
            "id": "T9",
            "what": "Two fixes committed without tests",
            "handled": all(by_ref.get(d, {}).get("accepted") for d in ("BILL-1187", "BILL-1203")),
            "how": "Shown on the risk card; a proven test for each",
        },
        {
            "id": "T10",
            "what": "A billing path no user can reach",
            "handled": any(d["name"] == "PercentCompleteBilling" for d in result["dead_code"])
            and not any("PercentComplete" in t["title"] for t in tests["tests"]),
            "how": "Listed as dead code by reachability; no test proposed",
        },
    ]


def scorecard(db: Connection) -> dict[str, Any]:
    result = analysis()
    tests = tests_api.tests()
    flaky = maintenance_api.flaky_tests(db)
    repair = maintenance_api.maintenance_measure(db)
    pr = review_api.pull_request(db)
    minutes = {str(c["id"]): c["manual_minutes"] for c in _key("manual_cases.yaml")["cases"]}
    intake = tests["intake"]
    accepted = [t for t in tests["tests"] if t["accepted"]]
    automated_cases = [t["ref"] for t in accepted if t["kind"] == "Manual case"]
    automated_cases += [e["case"] for e in intake if e["outcome"] in ("merged", "already_automated")]
    runs = maintenance_api._runs(maintenance_api.maintenance.RESULTS / "flaky-fix-runs.jsonl")
    run_seconds = sum(r["seconds"] for r in runs) / len(runs) if runs else None
    faults_total = sum(len(r["faults"]) for r in result["coverage"])
    caught_before = {f["id"] for r in result["coverage"] for f in r["faults"] if f["caught"]}
    caught_after = caught_before | {
        f for t in accepted for f in t["attempts"][-1]["checks"]["faults"]["caught"]
    }
    before_flaky = [
        {"test": t["test"]["title"], "failed": t["test"]["failed"], "runs": t["test"]["runs"]}
        for t in flaky["tests"]
    ]
    merged = pr["merged"]
    return {
        "manual_regression": {
            "total_minutes": sum(minutes.values()),
            "cases": len(minutes),
            "automated_cases": sorted(automated_cases),
            "automated_minutes": sum(minutes[c] for c in automated_cases),
            "suite_run_seconds": round(run_seconds, 1) if run_seconds else None,
            "suite_tests": flaky["suite_after"],
            "assumption": "Manual minutes per case were recorded by the quality engineering lead.",
        },
        "coverage": {
            "before": tests["coverage_before"],
            "after": {
                k: tests["coverage_after"][k] for k in ("critical_covered", "critical_rules", "percent")
            },
            "gate_percent": get_settings().gate_percent,
            "newly_covered": tests["coverage_after"]["newly_covered"],
        },
        "defects_detected": {
            "faults": faults_total,
            "caught_before": len(caught_before),
            "caught_after": len(caught_after),
            "t1_t2_caught": {"F04a", "F04b", "F04c", "F04d", "F07a", "F07b"} <= caught_after,
        },
        "escaped_defects": {"measured": False, "note": "Measured after release, in a pilot."},
        "reliability": {
            "before": before_flaky,
            "after_runs": flaky["runs_after"],
            "after_tests": flaky["suite_after"],
            "after_failures": flaky["failures_after"],
        },
        "maintenance": {
            "broken_tests": len(repair.get("failures") or []),
            "machine_seconds": (repair.get("timing") or {}).get("machine_seconds"),
            "approved": repair.get("review"),
        },
        "engineer": {
            "accepted": len([i for i in pr["items"] if (i["decision"] or {}).get("decision") == "approved"]),
            "rejected": len([i for i in pr["items"] if (i["decision"] or {}).get("decision") == "rejected"]),
            "items": len(pr["items"]),
            "merged": merged,
        },
        "planted": _planted(tests, flaky, result),
    }


@router.get("/gaps")
def gap_list(db: Db) -> dict[str, Any]:
    return gaps(db)


@router.get("/scorecard")
def score(db: Db) -> dict[str, Any]:
    return scorecard(db)


@router.get("/pack")
def evidence_pack(db: Db) -> dict[str, Any]:
    """Everything a reviewer outside the workbench needs, in one file."""
    tests = tests_api.tests()
    return {
        "format": "test-assurance-evidence/1",
        "area": "Project billing",
        "module": "Project Billing 4.8",
        "created_at": datetime.now(UTC).isoformat(),
        "scorecard": scorecard(db),
        "gaps": gaps(db),
        "approved_context": _approved_context(db),
        "tests": [
            {
                "id": t["id"],
                "title": t["title"],
                "source": {"kind": t["kind"], "ref": t["ref"]},
                "accepted": t["accepted"],
                "attempts": [
                    {"attempt": a["attempt"], "checks": a["checks"], "problems": a["problems"]}
                    for a in t["attempts"]
                ],
                "code": t["attempts"][-1]["generated"]["code"],
            }
            for t in tests["tests"]
        ],
        "flaky": maintenance_api.flaky_tests(db),
        "maintenance": maintenance_api.maintenance_measure(db),
        "pull_request": review_api.pull_request(db),
        "audit_trail_intact": audit.verify_chain(db),
    }
