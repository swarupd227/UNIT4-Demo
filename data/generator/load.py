"""Loads the generated files into Postgres. Safe to re-run: every table is replaced."""

from pathlib import Path

import psycopg

from app.config import get_settings

LOAD_ORDER = {
    "studio": [
        "customer",
        "legal_entity",
        "migration_case",
        "estate_item",
        "usage_event",
        "j2x_explanation",
        "mapping_precedent",
        "agent_signal",
        "reference_document",
    ],
    "cr_source": [
        "account",
        "account_map",
        "dimension_value",
        "dimension_map",
        "customer",
        "supplier",
        "resource_reference",
        "utilisation_summary",
        "project",
        "wip_item",
        "ar_open_item",
        "ap_open_item",
        "fx_rate",
        "gl_balance",
    ],
    "erpx_sim": [
        "account",
        "dimension_value",
        "customer",
        "supplier",
        "project",
        "fx_rate",
        "ar_open_item",
        "ap_open_item",
        "wip_item",
        "gl_balance",
        "utilisation_summary",
    ],
    "answer_key": ["expected_decision", "planted_issue"],
}


def load_all(root: Path) -> None:
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        for schema, tables in LOAD_ORDER.items():
            names = ", ".join(f"{schema}.{table}" for table in tables)
            cursor.execute(f"TRUNCATE {names} CASCADE")
        for schema, tables in LOAD_ORDER.items():
            for table in tables:
                path = root / schema / f"{table}.csv"
                with path.open("rb") as f:
                    header = f.readline().decode("utf-8").strip()
                    with cursor.copy(
                        f"COPY {schema}.{table} ({header}) FROM STDIN WITH (FORMAT csv)"
                    ) as copy:
                        while chunk := f.read(1 << 16):
                            copy.write(chunk)
        print("Loaded dataset into Postgres")
