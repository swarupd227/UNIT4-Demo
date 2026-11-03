"""Coverage of the business rules by the existing automated tests, measured by the fault check.

Plain code only. A test belongs to the rule named at the start of its title. A rule's score is the
share of its seeded faults that its own tests catch, where a catch is a failure confirmed on fresh
databases by the lab. A critical rule is covered when its score reaches the gate.
"""

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qe.engines.estate import Estate

TITLE_PATTERN = re.compile(r"""^\s*test\(\s*(['"`])(.+?)\1""", re.MULTILINE)
RULE_PATTERN = re.compile(r"^(BR-\d{2})\b")


@dataclass
class RuleCoverage:
    rule: str
    title: str
    critical: bool
    tests: list[dict[str, Any]] = field(default_factory=list)
    faults: list[dict[str, Any]] = field(default_factory=list)
    score: int | None = None
    covered: bool = False

    @property
    def caught(self) -> int:
        return sum(1 for fault in self.faults if fault["caught"])


def automated_tests(estate: Estate) -> list[dict[str, Any]]:
    found = []
    for path in estate.test_files():
        for match in TITLE_PATTERN.finditer(path.read_text(encoding="utf-8")):
            title = match.group(2)
            rule = RULE_PATTERN.match(title)
            found.append(
                {
                    "title": title,
                    "rule": rule.group(1) if rule else None,
                    "file": path.relative_to(estate.tests / "specs").as_posix(),
                }
            )
    return found


def _read_runs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _rule_of(title: str) -> str | None:
    match = RULE_PATTERN.match(title)
    return match.group(1) if match else None


def failures_by_build(results: Path) -> dict[str, set[str]]:
    """The rules whose tests failed on each faulted build, after the lab's confirmation reruns."""
    failed: dict[str, set[str]] = defaultdict(set)
    for run in _read_runs(results / "fault-check.jsonl"):
        for test in run["tests"]:
            if test["status"] == "failed" and (rule := _rule_of(test["title"])):
                failed[run["build"]].add(rule)
    return failed


def flaky_rates(results: Path) -> dict[str, dict[str, int]]:
    """Failures per test over the repeat runs of the unchanged module. Any failure there is flakiness."""
    runs = _read_runs(results / "baseline-20.jsonl")
    failed = Counter(test["title"] for run in runs for test in run["tests"] if test["status"] == "failed")
    return {title: {"failed": count, "runs": len(runs)} for title, count in failed.items()}


def coverage_map(estate: Estate, faults_file: Path, results: Path, gate_percent: int) -> list[RuleCoverage]:
    faults = yaml.safe_load(faults_file.read_text(encoding="utf-8"))["faults"]
    failed = failures_by_build(results)
    flaky = flaky_rates(results)
    rows = {
        rule["id"]: RuleCoverage(rule["id"], rule["title"], bool(rule["critical"])) for rule in estate.rules()
    }
    for test in automated_tests(estate):
        if test["rule"] in rows:
            rows[test["rule"]].tests.append({**test, "flaky": flaky.get(test["title"])})
    for fault in faults:
        row = rows[fault["rule"]]
        row.faults.append(
            {
                "id": fault["id"],
                "description": fault["description"],
                "caught": bool(row.tests) and fault["rule"] in failed.get(fault["id"], set()),
            }
        )
    for row in rows.values():
        if row.faults:
            row.score = round(100 * row.caught / len(row.faults))
        row.covered = bool(row.tests) and row.score is not None and row.score >= gate_percent
    return list(rows.values())


def summary(rows: list[RuleCoverage]) -> dict[str, Any]:
    critical = [row for row in rows if row.critical]
    covered = [row.rule for row in critical if row.covered]
    return {
        "critical_rules": len(critical),
        "critical_covered": len(covered),
        "percent": round(100 * len(covered) / len(critical)) if critical else 0,
        "covered": covered,
        "not_covered": [row.rule for row in critical if not row.covered],
    }
