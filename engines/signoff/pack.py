"""The customer sign-off pack: one PDF, plus the evidence files and a manifest of their hashes.

The scope is the trial migration of one entity, with listed exceptions. It never states cutover
readiness, because parallel runs and cutover need Unit4 and customer approval.
"""

import csv
import hashlib
import html
import io
import json
import zipfile
from typing import Any

from sqlalchemy import Connection, text
from weasyprint import HTML

from engines.validation.runner import current_input_hash

SCOPE = "Trial migration of the UK entity, with the listed exceptions. This is not cutover approval."


def gate(db: Connection) -> list[dict[str, Any]]:
    """What must be true before a customer may sign."""
    open_questions = db.execute(
        text("SELECT count(*) FROM studio.customer_question WHERE status = 'open'")
    ).scalar_one()
    run = db.execute(
        text("SELECT run_id, input_hash FROM studio.check_run ORDER BY run_id DESC LIMIT 1")
    ).first()
    checks = (
        db.execute(
            text("""
                SELECT r.check_id, r.status, count(e.exception_id) AS exceptions
                FROM studio.check_result r
                LEFT JOIN studio.exception e USING (run_id, check_id)
                WHERE r.run_id = :run_id GROUP BY 1, 2
            """),
            {"run_id": run.run_id},
        ).all()
        if run
        else []
    )
    current = run is not None and run.input_hash == current_input_hash(db)
    waiting = [c.check_id for c in checks if c.status == "waiting"]
    unlisted = [c.check_id for c in checks if c.status == "fail" and c.exceptions == 0]
    return [
        {
            "key": "questions",
            "label": "Every customer question is answered",
            "passed": open_questions == 0,
            "detail": f"{open_questions} open" if open_questions else "None open",
        },
        {
            "key": "reconciliation",
            "label": "Reconciliation has run on the current data and decisions",
            "passed": current,
            "detail": "Current" if current else "Needs a run" if run is None else "Out of date: run it again",
        },
        {
            "key": "rule_tests",
            "label": "Business rule tests have a result",
            "passed": run is not None and not waiting,
            "detail": "Waiting for the threshold" if waiting else "Complete" if run else "Not run",
        },
        {
            "key": "exceptions",
            "label": "Every failed check has a listed exception",
            "passed": run is not None and not unlisted,
            "detail": f"Unlisted: {', '.join(unlisted)}" if unlisted else "All listed" if run else "Not run",
        },
    ]


def _csv(header: list[str], rows: list[Any]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _money(minor: int | None) -> str:
    return "" if minor is None else f"£{minor / 100:,.2f}"


def _gather(db: Connection, run_id: int) -> dict[str, Any]:
    params = {"run_id": run_id}
    return {
        "decisions": db.execute(
            text("""
                SELECT d.item_id, e.name, e.item_type, d.outcome, d.status, p.outcome AS proposed_outcome,
                       p.reason, d.edit_reason,
                       (SELECT string_agg(a.person, '; ' ORDER BY a.decided_at) FROM studio.approval a
                        WHERE a.item_id = d.item_id) AS approved_by
                FROM studio.decision d
                JOIN studio.estate_item e USING (item_id)
                JOIN studio.proposal p USING (item_id)
                ORDER BY d.item_id
            """)
        ).all(),
        "checks": db.execute(
            text("SELECT * FROM studio.check_result WHERE run_id = :run_id ORDER BY check_id"), params
        ).all(),
        "exceptions": db.execute(
            text("""
                SELECT e.*, r.approved_by, r.approved_at
                FROM studio.exception e LEFT JOIN studio.exception_resolution r USING (code, title)
                WHERE e.run_id = :run_id ORDER BY e.exception_id
            """),
            params,
        ).all(),
        "questions": db.execute(
            text("SELECT * FROM studio.customer_question ORDER BY asked_at, question_id")
        ).all(),
        "audit": db.execute(
            text("SELECT seq, at, actor, role, action, item_id, hash FROM studio.audit_event ORDER BY seq")
        ).all(),
        "run": db.execute(text("SELECT * FROM studio.check_run WHERE run_id = :run_id"), params).one(),
        "case": db.execute(
            text("""
                SELECT k.name AS customer, c.label
                FROM studio.migration_case c JOIN studio.customer k USING (customer_id)
                LIMIT 1
            """)
        ).one(),
    }


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    decisions = data["decisions"]
    return {
        "decisions": len(decisions),
        "agreed": sum(row.status == "agreed" for row in decisions),
        "seeded_history": sum(row.action == "accepted_seeded" for row in data["audit"]),
        "checks": len(data["checks"]),
        "checks_passed": sum(row.status == "pass" for row in data["checks"]),
        "exceptions": len(data["exceptions"]),
        "questions_answered": sum(row.status == "answered" for row in data["questions"]),
        "audit_events": len(data["audit"]),
    }


def _table(header: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(cell)}</th>" for cell in header)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


CSS = """
@page { size: A4; margin: 18mm 16mm; @bottom-right { content: counter(page) " of " counter(pages);
        font: 9pt 'Liberation Sans'; color: #6b6258; } }
body { font: 10pt/1.45 'Liberation Sans', sans-serif; color: #1e1a16; }
h1 { font-size: 24pt; margin: 0 0 4pt; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; border-bottom: 1pt solid #cfc7bb; padding-bottom: 3pt; }
.lead { color: #4f483f; font-size: 11pt; }
.scope { background: #f6f3ee; padding: 8pt 10pt; margin: 10pt 0; }
table { width: 100%; border-collapse: collapse; font-size: 9pt; }
th { text-align: left; border-bottom: 1pt solid #1e1a16; padding: 3pt 4pt; }
td { border-bottom: .5pt solid #e4ded5; padding: 3pt 4pt; vertical-align: top; }
"""


def _render_pdf(data: dict[str, Any], summary: dict[str, Any], audit_head: str) -> bytes:
    case = data["case"]
    run = data["run"]
    checks = _table(
        ["Check", "Name", "Compares", "Result"],
        [[c.check_id, c.name, c.compares, c.status.capitalize()] for c in data["checks"]],
    )
    exceptions = _table(
        ["ID", "Exception", "Cause", "Proposed action", "Amount", "Approved by"],
        [
            [
                e.exception_id,
                e.title,
                e.cause,
                e.proposed_action,
                _money(e.amount_minor),
                e.approved_by or "Open",
            ]
            for e in data["exceptions"]
        ],
    )
    questions = _table(
        ["Item", "Question", "Answer", "Answered by"],
        [[q.item_id, q.question, q.answer or "Open", q.answered_by or ""] for q in data["questions"]],
    )
    counts: dict[str, int] = {}
    for row in data["decisions"]:
        key = row.outcome or "held"
        counts[key] = counts.get(key, 0) + 1
    decisions = _table(
        ["Outcome", "Items"], [[key.replace("_", " ").capitalize(), n] for key, n in sorted(counts.items())]
    )
    document = f"""
    <html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
    <h1>Customer sign-off pack</h1>
    <p class="lead">{html.escape(case.customer)} · {html.escape(case.label)} · CR to ERPx</p>
    <p class="scope"><strong>Scope.</strong> {SCOPE} Sandbox environment: test data only.</p>
    <h2>Summary</h2>
    {
        _table(
            ["Measure", "Value"],
            [
                ["Decisions agreed", f"{summary['agreed']} of {summary['decisions']}"],
                ["Of which accepted in earlier sessions", summary["seeded_history"]],
                ["Checks passed", f"{summary['checks_passed']} of {summary['checks']}"],
                ["Exceptions listed", summary["exceptions"]],
                ["Customer questions answered", summary["questions_answered"]],
                ["Audit events", summary["audit_events"]],
            ],
        )
    }
    <h2>Decision register</h2>
    <p>The full register is in decision_register.csv.</p>
    {decisions}
    <h2>Reconciliation report</h2>
    {checks}
    <p>Result hash {run.result_hash}<br>Input hash {run.input_hash}<br>
    Definitions hash {run.definitions_hash}</p>
    <h2>Exception log</h2>
    {exceptions}
    <h2>Customer questions</h2>
    {questions}
    <h2>Audit</h2>
    <p>The audit trail is hash-chained. The chain head when this pack was generated:<br>{audit_head}</p>
    </body></html>
    """
    return HTML(string=document).write_pdf()


def workflow_pack_html(customer: str, pack: dict[str, Any], usage: dict[str, int]) -> str:
    """The one page the customer's finance lead decides from."""
    proposed = _table(
        ["Workflow", "Rule", "Replaces", "Uses in 12 months", "ERPx configuration"],
        [
            [
                f"{workflow['name']} ({workflow['keeps']})",
                workflow["rule"],
                ", ".join(workflow["absorbs"]) or "None",
                f"{sum(usage.get(item, 0) for item in [workflow['keeps'], *workflow['absorbs']]):,}",
                "; ".join(workflow["erpx_configuration"]),
            ]
            for workflow in pack["proposed"]
        ],
    )
    controls = "".join(f"<li>{html.escape(line)}</li>" for line in pack["control_impact"])
    tests = _table(
        ["Test", "Case", "Expected"],
        [[test["id"], test["description"], test["expected"]] for test in pack["tests"]],
    )
    return f"""
    <html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
    <h1>Workflow decision pack</h1>
    <p class="lead">{html.escape(customer)} · CR to ERPx</p>
    <p class="scope"><strong>Decision needed.</strong> {html.escape(pack["decision_needed"])}</p>
    <h2>From {pack["from_count"]} workflows to {pack["to_count"]}</h2>
    {proposed}
    <p>Retire: {html.escape(", ".join(pack["retire"]))}</p>
    <h2>Control impact</h2>
    <ul>{controls}</ul>
    <h2>Test cases</h2>
    {tests}
    </body></html>
    """


def render_workflow_pack(customer: str, pack: dict[str, Any], usage: dict[str, int]) -> bytes:
    return HTML(string=workflow_pack_html(customer, pack, usage)).write_pdf()


def build_pack(db: Connection, run_id: int) -> dict[str, Any]:
    data = _gather(db, run_id)
    summary = _summary(data)
    audit_head = data["audit"][-1].hash
    files = {
        "decision_register.csv": _csv(
            [
                "item_id",
                "name",
                "type",
                "outcome",
                "status",
                "proposed_outcome",
                "reason",
                "edit_reason",
                "approved_by",
            ],
            [tuple(row) for row in data["decisions"]],
        ),
        "reconciliation.csv": _csv(
            ["check_id", "version", "name", "status", "source_value", "target_value", "differences"],
            [
                (c.check_id, c.version, c.name, c.status, c.source_value, c.target_value, c.difference_count)
                for c in data["checks"]
            ],
        ),
        "exception_log.csv": _csv(
            [
                "exception_id",
                "check_id",
                "title",
                "cause",
                "proposed_action",
                "approver_role",
                "amount_minor",
                "approved_by",
                "approved_at",
            ],
            [
                (
                    e.exception_id,
                    e.check_id,
                    e.title,
                    e.cause,
                    e.proposed_action,
                    e.approver_role,
                    e.amount_minor,
                    e.approved_by,
                    e.approved_at,
                )
                for e in data["exceptions"]
            ],
        ),
        "test_evidence.json": json.dumps(
            {c.check_id: c.summary for c in data["checks"] if c.check_id in ("R7", "R8")},
            indent=2,
            sort_keys=True,
            default=str,
        ).encode(),
        "customer_questions.csv": _csv(
            ["item_id", "question", "status", "answer", "answered_by", "answered_at"],
            [
                (q.item_id, q.question, q.status, q.answer, q.answered_by, q.answered_at)
                for q in data["questions"]
            ],
        ),
        "audit_trail.csv": _csv(
            ["seq", "at", "actor", "role", "action", "item_id", "hash"], [tuple(row) for row in data["audit"]]
        ),
    }
    files["signoff_pack.pdf"] = _render_pdf(data, summary, audit_head)

    manifest = {
        "scope": SCOPE,
        "audit_head": audit_head,
        "result_hash": data["run"].result_hash,
        "files": {name: _sha256(content) for name, content in sorted(files.items())},
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, content in sorted(files.items()):
            bundle.writestr(name, content)
        bundle.writestr("manifest.json", manifest_bytes)
    return {
        "pdf": files["signoff_pack.pdf"],
        "zip": archive.getvalue(),
        "manifest": manifest,
        "manifest_hash": _sha256(manifest_bytes),
        "audit_head": audit_head,
        "summary": summary,
    }
