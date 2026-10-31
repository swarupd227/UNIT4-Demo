"""Shared constants and deterministic file output."""

import csv
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SEED = 20261031
ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
GENERATED = ROOT / "generated"

CUSTOMER_ID = "ACG"
CASE_ID = "MC-017"
UK = "GB01"
NL = "NL01"
US = "US01"
DORMANT_NL = "NL02"

WINDOW_START = date(2025, 11, 1)
WINDOW_END = date(2026, 10, 31)
PERIODS = [f"{2025 + (m > 12)}{(m - 1) % 12 + 1:02d}" for m in range(11, 23)]

# Two CR accounts that merge into one ERPx account but carry different VAT codes (M6).
M6_ACCOUNT_A = "410020"
M6_ACCOUNT_B = "410021"
AR_CONTROL = "120000"
AP_CONTROL = "210000"
WIP_CONTROL = "130000"
BANK = "100000"

# A service line stored twice, once with trailing spaces (M9).
M9_VALUE = "ADVRISK"
M9_DUPLICATE = "ADVRISK  "

M7_DIFFERENCE_MINOR = 124050
FX_RATES = {"EUR": "0.871654", "USD": "0.742100"}

Table = tuple[list[str], list[tuple[Any, ...]]]


def rng(name: str) -> random.Random:
    """A stream per domain, so changing one generator leaves the others unchanged."""
    return random.Random(f"{SEED}:{name}")


def random_date(r: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=r.randint(0, (end - start).days))


def multiply_rate(amount_minor: int, rate_text: str) -> int:
    """amount × rate in exact integer arithmetic, rounded half away from zero."""
    whole, _, fraction = rate_text.partition(".")
    scale = 10 ** len(fraction)
    rate = int(whole + fraction)
    sign = -1 if amount_minor < 0 else 1
    return sign * ((2 * abs(amount_minor) * rate + scale) // (2 * scale))


def round_rate(rate_text: str, decimals: int) -> str:
    whole, _, fraction = rate_text.partition(".")
    scale = 10 ** (len(fraction) - decimals)
    rounded = (int(whole + fraction) * 2 + scale) // (2 * scale)
    digits = str(rounded).rjust(decimals + 1, "0")
    return f"{digits[:-decimals]}.{digits[-decimals:]}"


def write_table(path: Path, table: Table) -> None:
    header, rows = table
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def read_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def build_manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
