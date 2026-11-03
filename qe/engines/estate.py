"""Reads the billing module's estate as it is on disk: rules, manual cases, tests, defects and code.

Everything here is counted by plain code from the files, so the area card never shows a figure
that an agent made up.
"""

import csv
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CODE_SUFFIXES = (".cs", ".cshtml")
BUILD_FOLDERS = {"bin", "obj", "node_modules"}
TEST_PATTERN = re.compile(r"^\s*test\(", re.MULTILINE)


@dataclass(frozen=True)
class Estate:
    root: Path

    @property
    def source(self) -> Path:
        return self.root / "src"

    @property
    def tests(self) -> Path:
        return self.root / "tests" / "e2e"

    def rules(self) -> list[dict[str, Any]]:
        document = yaml.safe_load(
            (self.root / "docs" / "rules" / "business-rules.yaml").read_text(encoding="utf-8")
        )
        return list(document["rules"])

    def manual_cases(self) -> list[dict[str, Any]]:
        """Azure DevOps exports one row per step. A new case starts on a row with an ID."""
        path = self.root / "manual-cases" / "billing-manual-cases.csv"
        if not path.exists():
            return []
        cases: list[dict[str, Any]] = []
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("ID"):
                    cases.append({"id": row["ID"], "title": row["Title"], "steps": []})
                if cases and (row.get("Step Action") or row.get("Step Expected")):
                    cases[-1]["steps"].append(
                        {"action": row["Step Action"], "expected": row["Step Expected"]}
                    )
        return cases

    def defects(self) -> list[dict[str, str]]:
        path = self.root / "defects" / "billing-defects.csv"
        if not path.exists():
            return []
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_files(self) -> list[Path]:
        return sorted((self.tests / "specs").rglob("*.spec.ts"))

    def automated_tests(self) -> int:
        return sum(len(TEST_PATTERN.findall(path.read_text(encoding="utf-8"))) for path in self.test_files())

    def code_files(self) -> list[Path]:
        found: list[Path] = []
        for folder, subfolders, files in os.walk(self.source):
            # Build output is not code, and walking it is slow.
            subfolders[:] = [name for name in subfolders if name not in BUILD_FOLDERS]
            found += [Path(folder) / name for name in files if name.endswith(CODE_SUFFIXES)]
        return sorted(found)

    def code_lines(self) -> int:
        return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in self.code_files())

    def help_pages(self) -> int:
        folder = self.root / "docs" / "help"
        return len([p for p in folder.glob("*.md") if not p.name.startswith("00-")]) if folder.exists() else 0


@lru_cache
def estate(root: str) -> Estate:
    return Estate(Path(root))
