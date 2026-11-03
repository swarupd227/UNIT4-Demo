"""Flaky tests, found and measured by plain code from repeat runs of the unchanged module.

Every failure on the unchanged module is flakiness, because the code and the seeded data are the same
in every run. For each flaky test this gathers what a person would look at first: how often it fails
and with which message, which other tests were running at the same moment when it failed and when it
passed, and which tests read or change the same seeded data.
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from qe.engines import conventions
from qe.engines.estate import Estate

# Page object calls that change seeded data rather than only reading it.
WRITES = {"setDiscount": "the customer's agreement discount"}


def _runs(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _interval(test: dict[str, Any]) -> tuple[float, float] | None:
    if not test.get("started"):
        return None
    start = datetime.fromisoformat(test["started"].replace("Z", "+00:00")).timestamp()
    return start, start + test["durationMs"] / 1000


def _overlapping(run: dict[str, Any], title: str) -> set[str]:
    tests = {t["title"]: t for t in run["tests"]}
    mine = _interval(tests[title]) if title in tests else None
    if mine is None:
        return set()
    found = set()
    for other, test in tests.items():
        span = _interval(test)
        if other != title and span and span[0] < mine[1] and mine[0] < span[1]:
            found.add(other)
    return found


def _rule(title: str) -> str:
    return title.split(" ")[0]


def data_links(estate: Estate) -> dict[str, dict[str, Any]]:
    """For each existing test: the seeded data it names, the customers behind it, and what it changes."""
    suite = conventions.read_suite(estate)
    catalogue = yaml.safe_load((estate.root / "test-data" / "catalogue.yaml").read_text(encoding="utf-8"))
    customer_of = {f"{code} {p['name']}": p["customer"] for code, p in catalogue["projects"].items()}
    out = {}
    for path in estate.test_files():
        code = path.read_text(encoding="utf-8")
        title = conventions.TITLE.search(code)
        if not title:
            continue
        keys = sorted({f"{g}.{k}" for g, k in conventions.DATA_KEY.findall(code)})
        customers = set()
        for key in keys:
            group, name = key.split(".")
            value = suite.data_keys.get(group, {}).get(name, "")
            if group == "customers":
                customers.add(value)
            elif value in customer_of:
                customers.add(customer_of[value])
        out[title.group("title")] = {
            "file": path.relative_to(estate.tests).as_posix(),
            "data": keys,
            "customers": sorted(customers),
            "changes": [what for call, what in WRITES.items() if re.search(rf"\.{call}\(", code)],
        }
    return out


def triage(estate: Estate, runs_file: Path) -> list[dict[str, Any]]:
    runs = [run for run in _runs(runs_file) if run["tests"]]
    links = data_links(estate)
    failed_in: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        for test in run["tests"]:
            if test["status"] != "passed":
                failed_in[test["title"]].append(run)
    found = []
    for title, failing in sorted(failed_in.items()):
        passing = [
            run for run in runs if run not in failing and any(t["title"] == title for t in run["tests"])
        ]
        messages = Counter()
        for run in failing:
            test = next(t for t in run["tests"] if t["title"] == title)
            messages[(test["error"] or test["status"]).split("\n")[0]] += 1
        overlap_fail = Counter(o for run in failing for o in _overlapping(run, title))
        overlap_pass = Counter(o for run in passing for o in _overlapping(run, title))
        mine = links.get(title, {"customers": [], "data": [], "file": None, "changes": []})
        sharing = [
            {
                "test": other,
                "file": info["file"],
                "customers": sorted(set(info["customers"]) & set(mine["customers"])),
                "changes": info["changes"],
            }
            for other, info in links.items()
            if other != title and set(info["customers"]) & set(mine["customers"])
        ]
        found.append(
            {
                "title": title,
                "rule": _rule(title),
                "file": mine["file"],
                "failed": len(failing),
                "runs": len(runs),
                "messages": [{"message": m, "count": n} for m, n in messages.most_common()],
                "running_alongside": [
                    {
                        "test": other,
                        "when_failed": overlap_fail[other],
                        "failed_runs": len(failing),
                        "when_passed": overlap_pass[other],
                        "passed_runs": len(passing),
                    }
                    for other in sorted(set(overlap_fail) | set(overlap_pass))
                ],
                "shared_data": sharing,
                "timed": any(t.get("started") for run in runs for t in run["tests"]),
            }
        )
    return found
