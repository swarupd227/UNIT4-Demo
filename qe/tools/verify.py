"""Checks the billing estate against the answer key before any agent sees it.

    python -m qe.tools.verify            checks the files: rules, cases, docs, faults, defects, history
    python -m qe.tools.verify --lab      also checks the lab results: fault catches and flaky rates

Exits with 1 and lists every failed check.
"""

import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
QE = ROOT / "qe"
ESTATE = QE / "estate"
SOURCE = ESTATE / "src" / "Billing.Web"
KEY = QE / "answer-key"
RESULTS = QE / "lab" / "results"

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("ok    " if condition else "FAIL  ") + message)
    if not condition:
        failures.append(message)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def code_text() -> dict[Path, str]:
    return {
        p: p.read_text(encoding="utf-8")
        for p in SOURCE.rglob("*")
        if p.suffix in (".cs", ".cshtml") and not ({"bin", "obj"} & set(p.parts))
    }


def rules() -> None:
    register = load(ESTATE / "docs" / "rules" / "business-rules.yaml")["rules"]
    check(len(register) == 20, f"20 business rules ({len(register)})")
    check(sum(r["critical"] for r in register) == 12, "12 critical rules")


def manual_cases() -> None:
    cases: list[dict] = []
    with (ESTATE / "manual-cases" / "billing-manual-cases.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["ID"]:
                cases.append({"id": row["ID"], "steps": []})
            cases[-1]["steps"].append((row["Step Action"], row["Step Expected"]))
    check(len(cases) == 40, f"40 manual cases ({len(cases)})")
    by_id = {c["id"]: c for c in cases}
    key = {str(c["id"]): c for c in load(KEY / "manual_cases.yaml")["cases"]}
    check(set(by_id) == set(key), "every manual case is in the answer key")
    planted = Counter(c["planted"] for c in key.values() if c.get("planted"))
    check(planted == Counter({"T4": 1, "T5": 1, "T8": 2}), f"T4, T5 and T8 planted once ({dict(planted)})")
    t5 = next(c for c in key.values() if c.get("planted") == "T5")
    check(by_id[str(t5["id"])]["steps"][-1][1].strip() == "Verify the invoice is correct.", "T5 ends vaguely")
    t8 = [str(c["id"]) for c in key.values() if c.get("planted") == "T8"]
    check(by_id[t8[0]]["steps"] == by_id[t8[1]]["steps"], "T8 cases have identical steps")
    wrong = [c["id"] for c in key.values() if not c["expected_correct"]]
    t4 = next(c for c in key.values() if c.get("planted") == "T4")
    check(wrong == [t4["id"]], "only the T4 case has a wrong expected result")


def hidden_rule() -> None:
    pattern = re.compile(
        r"awaiting approval|approvals page|write-downs?[^.\n]{0,80}(approv|10 ?%|threshold)", re.I
    )
    sources = list((ESTATE / "docs" / "help").glob("*.md"))
    sources += [ESTATE / "manual-cases" / "billing-manual-cases.csv"]
    sources += list((ESTATE / "tests" / "e2e").rglob("*.ts"))
    sources = [p for p in sources if "node_modules" not in p.parts]
    leaks = [p.name for p in sources if pattern.search(p.read_text(encoding="utf-8"))]
    check(not leaks, f"write-down approval rule appears in no document, case or test ({leaks or 'none'})")
    statement = next(
        r for r in load(ESTATE / "docs" / "rules" / "business-rules.yaml")["rules"] if r["id"] == "BR-07"
    )
    check("approv" not in statement["statement"].lower(), "the rule register does not state the approval")
    check(
        "WD_LIMIT = 0.10m" in (SOURCE / "Services" / "AdjustmentService.cs").read_text(encoding="utf-8"),
        "the code has the 10% limit",
    )


def faults() -> None:
    entries = load(QE / "faults" / "faults.yaml")["faults"]
    for fault in entries:
        text = (ESTATE / "src" / fault["file"]).read_text(encoding="utf-8")
        check(text.count(fault["find"]) == 1, f"{fault['id']} applies once to {fault['file']}")
    per_rule = Counter(f["rule"] for f in entries)
    check(len(per_rule) == 20, f"every rule has at least one seeded fault ({len(per_rule)} rules)")
    key = load(KEY / "answer_key.yaml")
    named = {f for t in key["existing_tests"].values() for f in t["catches"] + t.get("misses", [])}
    named |= set(key["uncaught_at_baseline"])
    check(named == {f["id"] for f in entries}, "the answer key accounts for every fault")


def dead_code() -> None:
    texts = code_text()
    users = [
        p.name
        for p, t in texts.items()
        if "PercentCompleteBilling" in t and p.name != "PercentCompleteBilling.cs"
    ]
    check(not users, f"PercentCompleteBilling is referenced nowhere else ({users or 'none'})")
    callers = [
        p.name for p, t in texts.items() if "PercentCompleteAmount(" in t and p.name != "BillingHelper.cs"
    ]
    check(callers == ["PercentCompleteBilling.cs"], "PercentCompleteAmount is only called by the dead class")


def tests() -> None:
    specs = [p for p in (ESTATE / "tests" / "e2e" / "specs").rglob("*.spec.ts")]
    count = sum(len(re.findall(r"^\s*test\(", p.read_text(encoding="utf-8"), re.M)) for p in specs)
    check(count == 12, f"12 existing automated tests ({count})")


def defects() -> None:
    path = ESTATE / "defects" / "billing-defects.csv"
    if not path.exists():
        check(False, "defect export exists")
        return
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    check(len(rows) == 120, f"120 defects ({len(rows)})")
    key = {d["id"]: d for d in load(KEY / "defects.yaml")["defects"]}
    touching = sorted(i for i, d in key.items() if any("RoundingHelper.cs" in f for f in d["files"]))
    expected = ["BILL-1046", "BILL-1063", "BILL-1088", "BILL-1121", "BILL-1187", "BILL-1203", "BILL-1219"]
    check(
        touching == expected, f"the 7 rounding defects are the only ones touching RoundingHelper ({touching})"
    )
    untested = sorted(i for i in expected if key[i]["tests_added"] == "none")
    check(untested == ["BILL-1187", "BILL-1203"], f"two rounding fixes have no test ({untested})")
    repo = QE / "history" / "repo"
    if repo.exists():
        hashes = set(
            subprocess.run(
                ["git", "-C", str(repo), "log", "--format=%H"], capture_output=True, text=True
            ).stdout.split()
        )
        missing = [r["ID"] for r in rows if r["Linked Commit"] not in hashes]
        check(not missing, f"every defect links to a commit in the history ({len(missing)} missing)")
        for defect in expected:
            # Azure DevOps exports the bare work item number.
            commit = next(r["Linked Commit"] for r in rows if f"BILL-{r['ID']}" == defect)
            files = subprocess.run(
                ["git", "-C", str(repo), "show", "--name-only", "--format=", commit],
                capture_output=True,
                text=True,
            ).stdout.split()
            check(
                any(f.endswith("RoundingHelper.cs") for f in files),
                f"{defect} fix commit changes RoundingHelper.cs",
            )
    else:
        check(False, "the history repository has been built")


def lab() -> None:
    key = load(KEY / "answer_key.yaml")
    faults_path = RESULTS / "fault-check.jsonl"
    if faults_path.exists():
        caught: dict[str, set[str]] = defaultdict(set)
        for line in faults_path.read_text(encoding="utf-8").splitlines():
            result = json.loads(line)
            for test in result["tests"]:
                if test["status"] == "failed":
                    caught[result["build"]].add(test["title"].split(" ")[0])
        for rule, test in key["existing_tests"].items():
            for fault in test["catches"]:
                check(rule in caught[fault], f"{fault} is caught by the {rule} test")
            for fault in test.get("misses", []):
                check(rule not in caught[fault], f"{fault} is missed by the {rule} test")
        for fault in key["uncaught_at_baseline"]:
            check(
                not caught[fault],
                f"{fault} is caught by no existing test ({sorted(caught[fault]) or 'none'})",
            )
    else:
        check(False, "the fault check has run")

    runs_path = RESULTS / "baseline-20.jsonl"
    if runs_path.exists():
        runs = [json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines()]
        failed = Counter(
            t["title"].split(" ")[0] for r in runs for t in r["tests"] if t["status"] == "failed"
        )
        check(len(runs) == 20 and all(r["tests"] for r in runs), "20 baseline runs completed")
        for rule in ("BR-01", "BR-09"):
            check(2 <= failed[rule] <= 14, f"{rule} is flaky at a measurable rate ({failed[rule]} of 20)")
        steady = {r: n for r, n in failed.items() if r not in ("BR-01", "BR-09")}
        check(not steady, f"no other test fails on the baseline ({steady or 'none'})")
    else:
        check(False, "the 20 baseline runs have run")


def main() -> None:
    rules()
    manual_cases()
    hidden_rule()
    faults()
    dead_code()
    tests()
    defects()
    if "--lab" in sys.argv:
        lab()
    print(f"\n{len(failures)} failed" if failures else "\nAll checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
