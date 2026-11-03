"""Runs one attempt of test generation, recording agent results for replay.

    python -m qe.engines.agents.generate 1     intake, case review, then a test for every source
    python -m qe.engines.agents.generate 2     a new test for each source whose attempt 1 test failed a check

Each attempt writes qe/generated/attempt-<n>: the candidates' spec files and test data, laid out like
the suite, and manifest.json with every candidate and its checks so far. The lab then proves the
attempt (npm run qe:prove -- <n>), and the next attempt reads those results.
"""

import json
import sys
from typing import Any

from qe.engines import analysis, generation
from qe.engines.agents.gateway import AgentRequest, ReplayGateway
from qe.engines.agents.record import GATE_PERCENT, HISTORY_REPO, QE_ROOT, RecordingGateway
from qe.engines.agents.schemas import CaseReview, GeneratedTest, TestValidation
from qe.engines.conventions import TITLE


def _check(src: analysis.Sources, request: AgentRequest, output: dict[str, Any]) -> Any:
    if request.agent == "case_validator":
        return generation.checked_review(request, output)
    if request.agent == "test_generator":
        return generation.checked_generation(output)
    if request.agent == "test_validator":
        return generation.checked_validation(request, output)
    return analysis.checked(src, request, output)


def _meta(result: Any) -> dict[str, Any]:
    return {"source": result.source, "model": result.model, "duration_ms": result.duration_ms}


def build(
    material: generation.Material,
    gateway: RecordingGateway,
    source: dict[str, Any],
    attempt: int,
    decided: list[dict[str, Any]],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    others = {c["generated"]["data"]["value"] for c in decided}
    other_keys = {
        f"{c['generated']['data']['group']}.{c['generated']['data']['key']}": c["generated"]["path"]
        for c in decided
    }
    request = generation.generator_request(material, source, attempt, others, previous)
    result = gateway.run(request, GeneratedTest)
    generated = generation.checked_generation(result.output)
    issues = generation.check_generated(material, source, generated, other_keys, others)
    v_request = generation.validator_request(material, source, attempt, generated)
    v_result = gateway.run(v_request, TestValidation)
    validation = generation.compare(generated, generation.checked_validation(v_request, v_result.output))
    title = TITLE.search(generated["code"])
    candidate = {
        "id": source["id"],
        "kind": source["kind"],
        "ref": source["ref"],
        "rule": source["rule"],
        "attempt": attempt,
        "title": title.group("title").replace("\\'", "'") if title else generated["title"],
        "generated": generated,
        "issues": issues,
        "validation": validation,
        "ready_for_lab": not issues and all(v["agrees"] for v in validation),
        "agents": {"generator": _meta(result), "validator": _meta(v_result)},
    }
    state = "ready for the lab" if candidate["ready_for_lab"] else "rejected before the lab"
    print(f"     {source['id']} attempt {attempt}: {state}", flush=True)
    return candidate


def first_attempt(material: generation.Material, gateway: RecordingGateway) -> list[dict[str, Any]]:
    intake = generation.intake(material)
    for entry in intake:
        if entry["outcome"] == "review":
            request = generation.case_request(material, entry["case"])
            result = gateway.run(request, CaseReview)
            entry["review"] = generation.checked_review(request, result.output)
            entry["outcome"] = entry["review"]["outcome"]
            entry["agent"] = _meta(result)
    path = generation.GENERATED / "intake.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(intake, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    ready = [e["case"] for e in intake if e["outcome"] == "ready"]
    candidates: list[dict[str, Any]] = []
    for source in generation.sources(material, ready):
        candidates.append(build(material, gateway, source, 1, candidates, None))
    return candidates


def next_attempt(
    material: generation.Material, gateway: RecordingGateway, attempt: int
) -> list[dict[str, Any]]:
    previous = generation.load_manifest(attempt - 1)
    if previous is None:
        raise SystemExit(f"Attempt {attempt - 1} has not run.")
    # Each candidate is judged on the lab run of the attempt that made it.
    labs = {n: generation.proof(n, material.src.faults_file) for n in range(1, attempt)}
    by_id = {
        s["id"]: s
        for s in generation.sources(
            material, [c["ref"] for c in previous["candidates"] if c["kind"] == "manual_case"]
        )
    }
    kept, redo = [], []
    for candidate in previous["candidates"]:
        ran = labs[candidate["attempt"]].get(candidate["title"]) if candidate["ready_for_lab"] else None
        verdict = generation.judge(candidate, ran)
        (kept if verdict["accepted"] else redo).append((candidate, verdict))
    decided = [c for c, _ in kept]
    existing = [p.relative_to(material.tests).as_posix() for p in material.src.estate.test_files()]
    for candidate, verdict in redo:
        source = by_id[candidate["id"]]
        in_use = existing + [c["generated"]["path"] for c in decided]
        feedback = generation.previous_attempt(candidate, verdict, in_use)
        decided.append(build(material, gateway, source, attempt, decided, feedback))
    order = [c["id"] for c in previous["candidates"]]
    return sorted(decided, key=lambda c: order.index(c["id"]))


def main() -> None:
    attempt = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    src = analysis.Sources.at(QE_ROOT, HISTORY_REPO, GATE_PERCENT)
    material = generation.Material(src, analysis.analyse(src, ReplayGateway(analysis.RECORDINGS)))
    gateway = RecordingGateway(lambda request, output: _check(src, request, output))
    candidates = (
        first_attempt(material, gateway) if attempt == 1 else next_attempt(material, gateway, attempt)
    )
    if gateway.failures:
        print(f"{len(gateway.failures)} agent results failed their checks; nothing was written.")
        sys.exit(1)
    folder = generation.write_overlay(material, attempt, candidates)
    manifest = {"attempt": attempt, "candidates": candidates}
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    ready = sum(1 for c in candidates if c["ready_for_lab"] and c["attempt"] == attempt)
    print(f"Attempt {attempt}: {ready} new candidates ready for the lab. Next: npm run qe:prove -- {attempt}")


if __name__ == "__main__":
    main()
