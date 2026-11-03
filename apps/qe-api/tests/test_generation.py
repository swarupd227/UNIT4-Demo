import json
from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient

from app.config import get_settings
from app.context import analysis
from app.main import app
from qe.engines import conventions, generation
from qe.engines.analysis import Sources

client = TestClient(app)
SETTINGS = get_settings()
KEY = yaml.safe_load((Path(SETTINGS.answer_key) / "answer_key.yaml").read_text(encoding="utf-8"))
SRC = Sources.at(Path(SETTINGS.estate_root).parent, Path(SETTINGS.history_repo), SETTINGS.gate_percent)


def _tests() -> dict[str, Any]:
    response = client.get("/api/tests")
    assert response.status_code == 200
    return response.json()


def test_intake_sends_t4_to_a_person_asks_t5_for_a_result_and_merges_t8() -> None:
    outcomes = {e["case"]: e for e in _tests()["intake"]}
    assert outcomes["48207"]["outcome"] == "to_person"
    assert outcomes["48230"]["outcome"] == "needs_expected_result"
    assert outcomes["48229"]["outcome"] == "merged" and outcomes["48229"]["into"] == "48208"
    assert outcomes["48208"]["outcome"] == "already_automated"
    ready = {case for case, e in outcomes.items() if e["outcome"] == "ready"}
    assert ready == {"48212", "48218", "48219", "48222", "48224"}
    # Found by the validator, not planted: the case expects a message the posting page now shows.
    assert outcomes["48236"]["outcome"] == "to_person"


def test_t4_disagreement_is_the_rounded_total() -> None:
    review = next(e for e in _tests()["intake"] if e["case"] == "48207")["review"]
    disagreeing = [s for s in review["steps"] if s["verdict"] == "disagrees"]
    assert any("11,183.26" in s["expected"] for s in disagreeing)


def test_every_accepted_test_passes_all_four_checks() -> None:
    tests = _tests()["tests"]
    assert len(tests) == 10
    for test in tests:
        last = test["attempts"][-1]
        assert test["accepted"], f"{test['id']} was not accepted: {last['problems']}"
        assert all(check["passed"] for check in last["checks"].values())
        assert last["checks"]["stability"]["passed_runs"] == last["checks"]["stability"]["runs"] >= 20


def test_t3_weak_test_is_rejected_by_the_fault_check_then_accepted() -> None:
    weak = next(t for t in _tests()["tests"] if t["ref"] == "48224")
    first, last = weak["attempts"][0], weak["attempts"][-1]
    assert first["checks"]["conventions"]["passed"] and first["checks"]["expected_results"]["passed"]
    assert first["checks"]["stability"]["passed"]
    assert not first["checks"]["faults"]["passed"] and first["checks"]["faults"]["caught"] == []
    assert last["accepted"] and "F14" in last["checks"]["faults"]["caught"]


def test_defect_tests_catch_the_fault_that_puts_their_defect_back() -> None:
    faults = {"BILL-1046": "F04a", "BILL-1121": "F04b", "BILL-1187": "F04c", "BILL-1203": "F04d"}
    for test in _tests()["tests"]:
        if test["ref"] in faults:
            assert faults[test["ref"]] in test["attempts"][-1]["checks"]["faults"]["caught"]


def test_coverage_moves_to_nine_of_twelve() -> None:
    after = _tests()["coverage_after"]
    assert (after["critical_covered"], after["percent"]) == (9, 75)
    assert sorted(after["newly_covered"]) == ["BR-04", "BR-07"]


def test_no_test_source_reaches_the_validator() -> None:
    material = generation.Material(SRC, analysis())
    ready = [
        e["case"]
        for e in json.loads((generation.GENERATED / "intake.json").read_text())
        if e["outcome"] == "ready"
    ]
    sources = {s["id"]: s for s in generation.sources(material, ready)}
    for entries in generation.history().values():
        for attempt in entries:
            request = generation.validator_request(
                material, sources[attempt["id"]], attempt["attempt"], attempt["generated"]
            )
            assert set(request.payload) == {"rule", "source", "scenario", "checks", "documents"}
            sent = json.dumps(request.payload)
            code_lines = [
                line.strip() for line in attempt["generated"]["code"].splitlines() if len(line.strip()) > 25
            ]
            assert not [line for line in code_lines if json.dumps(line)[1:-1] in sent]
            assert all(
                value["value"] not in request.payload["checks"] for value in attempt["generated"]["checks"]
            )


def test_conventions_catch_the_fixed_wait_in_the_existing_numbering_test() -> None:
    suite = conventions.read_suite(SRC.estate)
    path = SRC.estate.tests / "specs" / "invoicing" / "numbering.spec.ts"
    rule = next(r for r in SRC.estate.rules() if r["id"] == "BR-09")
    issues = conventions.check(
        suite, rule, "specs/invoicing/numbering.spec.ts", path.read_text(), "projects.pacificCustoms", {}
    )
    assert issues == ["Waits a fixed time instead of waiting for the page."]
