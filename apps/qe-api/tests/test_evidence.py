from fastapi.testclient import TestClient

from app.main import app
from qe.engines import review

client = TestClient(app)


def test_the_pull_request_carries_every_accepted_test_and_both_fixes() -> None:
    pr = client.get("/api/review").json()
    kinds = [item["kind"] for item in pr["items"]]
    assert kinds.count("test") == 10 and kinds.count("flaky_fix") == 2
    for item in pr["items"]:
        assert item["runs"] and all(run["status"] == "passed" for run in item["runs"])
        if item["kind"] == "test":
            assert all(v["agrees"] for v in item["validation"])
            assert item["faults"]["caught"]


def test_release_controls_are_unchanged() -> None:
    pr = client.get("/api/review").json()
    assert pr["release_controls_unchanged"]
    assert all(f["path"].startswith(review.TESTS) for f in pr["files"])


def test_only_an_engineer_decides_and_merges() -> None:
    url = "/api/review/items/MC-48212"
    assert client.post(url, json={"person_key": "qe_lead", "decision": "approved"}).status_code == 403
    assert client.post("/api/review/merge", json={"person_key": "full_circuit_owner"}).status_code == 403


def test_gaps_rank_the_rules_still_below_the_gate() -> None:
    gaps = client.get("/api/gaps").json()
    critical = [r["rule"] for r in gaps["below_gate"] if r["critical"]]
    assert sorted(critical) == ["BR-11", "BR-15", "BR-19"]
    assert {w["case"] for w in gaps["waiting_on_people"]} >= {"48207", "48230", "48236"}
    assert any(d["name"] == "PercentCompleteBilling" for d in gaps["dead_code"])


def test_scorecard_measures_and_every_planted_issue_is_handled() -> None:
    card = client.get("/api/scorecard").json()
    assert (card["coverage"]["before"]["percent"], card["coverage"]["after"]["percent"]) == (58, 75)
    assert card["defects_detected"]["t1_t2_caught"]
    assert card["defects_detected"]["caught_after"] > card["defects_detected"]["caught_before"]
    assert card["reliability"]["after_failures"] == 0 and card["reliability"]["after_runs"] == 20
    assert card["maintenance"]["machine_seconds"] > 0
    assert not card["escaped_defects"]["measured"]
    assert all(p["handled"] for p in card["planted"]), [p["id"] for p in card["planted"] if not p["handled"]]


def test_the_evidence_pack_holds_everything_and_the_audit_trail_is_intact() -> None:
    pack = client.get("/api/pack").json()
    assert pack["format"] == "test-assurance-evidence/1"
    assert len(pack["tests"]) == 10 and pack["audit_trail_intact"]
    assert {"scorecard", "gaps", "flaky", "maintenance", "pull_request"} <= set(pack)
