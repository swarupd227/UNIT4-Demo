"""Diagnoses flaky tests and repairs selectors, recording agent results for replay.

    python -m qe.engines.agents.maintain flaky     diagnose and fix each flaky test in the latest 20 runs
    python -m qe.engines.agents.maintain repair    repair the selectors the next release broke

Each writes its proposed files under qe/generated/maintenance/<name>, laid out like the suite, for the lab
to prove (npm run qe:maintain-lab -- flaky, release or repair).
"""

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from qe.engines import flaky, generation, maintenance
from qe.engines.agents.gateway import AgentRequest
from qe.engines.agents.record import QE_ROOT, RecordingGateway
from qe.engines.agents.schemas import FlakyDiagnosis, SelectorRepair
from qe.engines.estate import Estate

ESTATE = Estate(QE_ROOT / "estate")


def _check(request: AgentRequest, output: dict[str, Any]) -> Any:
    if request.agent == "flaky_diagnoser":
        return maintenance.checked_diagnosis(ESTATE, request, output)
    return maintenance.checked_repair(ESTATE, request, output)


def _meta(result: Any) -> dict[str, Any]:
    return {"source": result.source, "model": result.model, "duration_ms": result.duration_ms}


def suite_overlay() -> Path:
    """The suite as it stands after generation: the last attempt's candidates."""
    attempts = generation.attempts()
    return generation.GENERATED / f"attempt-{attempts[-1]}"


def diagnose(gateway: RecordingGateway) -> None:
    runs = generation.PROOF / f"attempt-{generation.attempts()[-1]}-runs.jsonl"
    found = [f for f in flaky.triage(ESTATE, runs) if 0 < f["failed"] < f["runs"] and f["file"]]
    diagnoses, files = [], []
    for item in found:
        request = maintenance.diagnoser_request(ESTATE, item)
        result = gateway.run(request, FlakyDiagnosis)
        diagnosis = maintenance.checked_diagnosis(ESTATE, request, result.output)
        diagnoses.append({"test": item, "diagnosis": diagnosis, "agent": _meta(result)})
        files += diagnosis["files"]
        print(f"     {item['rule']}: {diagnosis['cause']}: {diagnosis['fix_summary']}", flush=True)
    if gateway.failures:
        sys.exit(1)
    maintenance.write_overlay("flaky-fix", files, suite_overlay())
    maintenance.save("flaky", {"runs_file": runs.name, "diagnoses": diagnoses})
    print("Next: npm run qe:maintain-lab -- flaky")


def repair(gateway: RecordingGateway) -> None:
    releases = yaml.safe_load((QE_ROOT / "faults" / "releases.yaml").read_text(encoding="utf-8"))["releases"]
    release = releases[0]
    before = maintenance.RESULTS / f"{release['id']}-before.jsonl"
    runs = [json.loads(line) for line in before.read_text(encoding="utf-8").splitlines() if line]
    existing = {p.relative_to(ESTATE.tests / "specs").as_posix() for p in ESTATE.test_files()}
    failures = [
        {**t, "existing": t["file"] in existing}
        for run in runs
        for t in run["tests"]
        if t["status"] == "failed"
    ]
    request = maintenance.repairer_request(ESTATE, release, failures)
    result = gateway.run(request, SelectorRepair)
    fix = maintenance.checked_repair(ESTATE, request, result.output)
    if gateway.failures:
        sys.exit(1)
    maintenance.write_overlay(f"{release['id']}-repair", fix["files"], maintenance.OUT / "flaky-fix")
    maintenance.save(
        f"{release['id']}-repair",
        {"release": release, "failures": failures, "repair": fix, "agent": _meta(result)},
    )
    print(f"     {fix['fix_summary']}")
    print("Next: npm run qe:maintain-lab -- repair")


def main() -> None:
    gateway = RecordingGateway(_check)
    {"flaky": diagnose, "repair": repair}[sys.argv[1]](gateway)


if __name__ == "__main__":
    main()
