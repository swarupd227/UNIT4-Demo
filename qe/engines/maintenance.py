"""Reliability and maintenance: fixing flaky tests and repairing selectors a release broke.

Plain code finds the flaky tests and gathers the evidence (qe.engines.flaky), checks every proposed
change and lays it out for the lab, and reads the lab's results. Agents name the cause and write the
fix. The lab then proves the fix the same way as a new test: 20 runs on fresh databases.
"""

import json
from pathlib import Path
from typing import Any

import yaml

from qe.engines import conventions, flaky
from qe.engines.agents.gateway import AgentRequest
from qe.engines.agents.prompts import prompt_version
from qe.engines.agents.schemas import FlakyDiagnosis, SelectorRepair
from qe.engines.analysis import CheckFailed
from qe.engines.estate import Estate

QE_ROOT = Path(__file__).resolve().parents[1]
OUT = QE_ROOT / "generated" / "maintenance"
RESULTS = QE_ROOT / "lab" / "results" / "maintenance"
ALLOWED = ("specs/", "fixtures/", "pages/")
FORBIDDEN_FIXES = ("waitForTimeout(", "retries", "test.slow(", "timeout:")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _suite_files(estate: Estate, folder: str) -> dict[str, str]:
    return {
        p.relative_to(estate.tests).as_posix(): _text(p)
        for p in sorted((estate.tests / folder).rglob("*.ts"))
    }


def free_customers(estate: Estate) -> list[str]:
    """Customers whose projects no test uses, with their projects, for a test that must change data."""
    catalogue = yaml.safe_load(_text(estate.root / "test-data" / "catalogue.yaml"))
    links = flaky.data_links(estate)
    used = {c for info in links.values() for c in info["customers"]}
    suite = conventions.read_suite(estate)
    used |= {
        suite.data_keys["customers"].get(k.split(".")[1], "")
        for k in suite.data_in_use
        if k.startswith("customers.")
    }
    out = []
    for code, customer in catalogue["customers"].items():
        if code in used or customer["on_hold"]:
            continue
        projects = [
            f"{p} {info['name']}" for p, info in catalogue["projects"].items() if info["customer"] == code
        ]
        out.append(f"{code} {customer['name']}: projects {', '.join(projects) or 'none'}")
    return out


def diagnoser_request(estate: Estate, found: dict[str, Any]) -> AgentRequest:
    sharing = {s["file"] for s in found["shared_data"]}
    payload = {
        "conventions": conventions.read_suite(estate).summary(),
        "test": {
            "title": found["title"],
            "file": found["file"],
            "source": _text(estate.tests / found["file"]),
        },
        "failures": {"failed": found["failed"], "runs": found["runs"], "messages": found["messages"]},
        "running_alongside": found["running_alongside"],
        "shared_data": found["shared_data"],
        "other_tests": {path: _text(estate.tests / path) for path in sorted(sharing)},
        "page_objects": _suite_files(estate, "pages"),
        "fixtures": _suite_files(estate, "fixtures"),
        "test_data_catalogue": _text(estate.root / "test-data" / "catalogue.yaml"),
        "free_data": free_customers(estate),
        "help": _text(estate.root / "docs" / "help" / "22-finalising-an-invoice.md"),
    }
    return AgentRequest("flaky_diagnoser", found["rule"], prompt_version("flaky_diagnoser"), payload)


def repairer_request(estate: Estate, release: dict[str, Any], failures: list[dict[str, Any]]) -> AgentRequest:
    payload = {
        "release": release["description"],
        "markup_change": {
            "file": release["file"],
            "before": release["find"],
            "after": release["replace"],
        },
        "failures": [{"title": f["title"], "file": f["file"], "error": f["error"]} for f in failures],
        "page_objects": _suite_files(estate, "pages"),
        "failing_tests": {
            f"specs/{f['file']}": _text(estate.tests / "specs" / f["file"])
            for f in failures
            if f.get("existing")
        },
    }
    return AgentRequest("selector_repairer", release["id"], prompt_version("selector_repairer"), payload)


def check_files(estate: Estate, files: list[dict[str, str]], where: str, pages_only: bool = False) -> None:
    """A fix may change only the suite's own files, and may not hide the problem."""
    if not files:
        raise CheckFailed(f"{where}: changes no file")
    for change in files:
        allowed = ("pages/",) if pages_only else ALLOWED
        if not change["path"].startswith(allowed) or ".." in change["path"]:
            raise CheckFailed(f"{where}: may not change {change['path']}")
        before = _text(estate.tests / change["path"]) if (estate.tests / change["path"]).exists() else ""
        for pattern in FORBIDDEN_FIXES:
            if change["content"].count(pattern) > before.count(pattern):
                raise CheckFailed(f"{where}: adds {pattern.rstrip('(:')} instead of fixing the cause")


def checked_diagnosis(estate: Estate, request: AgentRequest, output: dict[str, Any]) -> dict[str, Any]:
    diagnosis = FlakyDiagnosis.model_validate(output).model_dump()
    check_files(estate, diagnosis["files"], f"flaky_diagnoser on {request.subject}")
    return diagnosis


def checked_repair(estate: Estate, request: AgentRequest, output: dict[str, Any]) -> dict[str, Any]:
    repair = SelectorRepair.model_validate(output).model_dump()
    check_files(estate, repair["files"], f"selector_repairer on {request.subject}", pages_only=True)
    return repair


def write_overlay(name: str, files: list[dict[str, str]], extra: Path | None = None) -> Path:
    """Lays the changed files out like the suite, over an earlier overlay if one is given."""
    folder = OUT / name
    if extra is not None:
        for source in extra.rglob("*"):
            if source.is_file() and source.name != "manifest.json":
                target = folder / source.relative_to(extra)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
    for change in files:
        target = folder / change["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(change["content"].rstrip() + "\n", encoding="utf-8", newline="\n")
    return folder


def save(name: str, record: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def load(name: str) -> dict[str, Any] | None:
    path = OUT / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
