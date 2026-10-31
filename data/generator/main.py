"""Builds the whole synthetic dataset. The same seed always gives byte-identical files."""

import argparse
import json
import shutil
from pathlib import Path

from data.generator import common, estate
from data.generator.common import (
    CASE_ID,
    CUSTOMER_ID,
    DORMANT_NL,
    FIXTURES,
    GENERATED,
    NL,
    ROOT,
    UK,
    US,
    WINDOW_END,
    WINDOW_START,
    Table,
    build_manifest,
    compact_json,
    read_table,
    write_json,
    write_table,
)
from data.generator.finance import generate_finance
from engines.migration.target import SimulatedErpxTarget
from engines.migration.trial_load import run_trial_load


def studio_tables() -> dict[str, Table]:
    return {
        "customer": (
            [
                "customer_id",
                "name",
                "sector",
                "staff_count",
                "erp_since",
                "cr_since",
                "modules_in_scope",
                "out_of_scope",
                "goal",
                "synthetic",
            ],
            [
                (
                    CUSTOMER_ID,
                    "Ardleigh Consulting Group",
                    "Professional services",
                    1800,
                    2009,
                    2021,
                    "Financials; Projects and billing; Time and expenses; Procurement",
                    "HR and payroll",
                    "Move from CR to ERPx and cut customisations before moving",
                    True,
                )
            ],
        ),
        "legal_entity": (
            [
                "entity_code",
                "customer_id",
                "name",
                "country",
                "base_currency",
                "status",
                "dormant_since",
                "in_migration_scope",
            ],
            [
                (
                    UK,
                    CUSTOMER_ID,
                    "Ardleigh Consulting UK Ltd",
                    "United Kingdom",
                    "GBP",
                    "trading",
                    None,
                    True,
                ),
                (
                    NL,
                    CUSTOMER_ID,
                    "Ardleigh Consulting Nederland B.V.",
                    "Netherlands",
                    "EUR",
                    "trading",
                    None,
                    False,
                ),
                (
                    DORMANT_NL,
                    CUSTOMER_ID,
                    "Ardleigh Advisory Holding B.V.",
                    "Netherlands",
                    "EUR",
                    "dormant",
                    "2023-06-30",
                    False,
                ),
                (US, CUSTOMER_ID, "Ardleigh Consulting Inc.", "United States", "USD", "trading", None, False),
            ],
        ),
        "migration_case": (
            ["case_id", "customer_id", "label", "entity_code", "status", "window_start", "window_end"],
            [(CASE_ID, CUSTOMER_ID, "Migration case 017", UK, "In review", WINDOW_START, WINDOW_END)],
        ),
    }


def generate(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    settings = json.loads((FIXTURES / "config" / "load_template.json").read_text(encoding="utf-8"))

    finance = generate_finance(settings["fx_rate_decimals"])
    for name, table in finance.items():
        write_table(output / "cr_source" / f"{name}.csv", table)

    source = {name: read_table(output / "cr_source" / f"{name}.csv") for name in finance}
    target = SimulatedErpxTarget()
    run_trial_load(source, settings, target)
    for name, table in target.objects.items():
        write_table(output / "erpx_sim" / f"{name}.csv", table)

    items = [
        *estate.generate_code_items(),
        *estate.generate_reports(),
        *estate.generate_workflows(),
        *estate.generate_integrations(),
        *estate.generate_config_items(),
    ]
    j2x_table, j2x_report = estate.generate_j2x(sorted(items, key=lambda item: item.item_id))
    item_table, event_table = estate.estate_rows(items, {row[0] for row in j2x_table[1]})

    for name, table in studio_tables().items():
        write_table(output / "studio" / f"{name}.csv", table)
    write_table(output / "studio" / "estate_item.csv", item_table)
    write_table(output / "studio" / "usage_event.csv", event_table)
    write_table(output / "studio" / "j2x_explanation.csv", j2x_table)
    write_table(output / "studio" / "mapping_precedent.csv", estate.generate_precedents())
    write_table(output / "studio" / "agent_signal.csv", estate.agent_signals(items))

    write_table(output / "answer_key" / "expected_decision.csv", estate.expected_rows(items))
    planted = json.loads((ROOT / "answer_key" / "planted_issues.json").read_text(encoding="utf-8"))
    columns = ["issue_id", "issue_type", "planted", "expected_behaviour", "item_ref", "check_ref", "scene"]
    write_table(
        output / "answer_key" / "planted_issue.csv",
        (columns, [tuple(p[c] for c in columns) for p in planted]),
    )

    policy = (FIXTURES / "documents" / "billing_policy.md").read_text(encoding="utf-8")
    documents = [
        ("billing_policy", compact_json({"text": policy})),
        ("erpx_standard_catalogue", compact_json(estate.standard_catalogue())),
        ("j2x_assessment", compact_json(j2x_report)),
    ]
    write_table(output / "studio" / "reference_document.csv", (["document_key", "content"], documents))

    write_json(output / "documents" / "j2x_assessment.json", j2x_report)
    write_json(output / "documents" / "erpx_standard_catalogue.json", estate.standard_catalogue())
    shutil.copyfile(FIXTURES / "documents" / "billing_policy.md", output / "documents" / "billing_policy.md")

    write_json(output / "manifest.json", {"seed": common.SEED, "files": build_manifest(output)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true", help="Also verify and load into Postgres")
    args = parser.parse_args()

    generate(GENERATED)
    print(f"Generated dataset in {GENERATED}")
    if args.load:
        from data.generator.load import load_all
        from data.generator.verify import verify

        if not verify(GENERATED):
            raise SystemExit("Verification failed; nothing was loaded.")
        load_all(GENERATED)
        from app.db import get_engine
        from engines.decision.seed import seed_decisions

        with get_engine().begin() as connection:
            seed_decisions(connection)
        print("Proposed decisions for the estate")


if __name__ == "__main__":
    main()
