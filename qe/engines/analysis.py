"""The context analysis of the billing area: plain code first, agents where reading is needed.

Plain code measures coverage, groups defects by the code their fixes touched, finds unreachable
code and checks every agent result. Agents map manual cases and defects to rules, write risk cards
and find rules the code enforces that no document states. Each agent result is checked here before
anyone sees it: every ID must exist, every code citation must resolve to a real line, and a hidden
rule's search phrases are looked for in the documents by plain text search.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from qe.engines import coverage, deadcode
from qe.engines import defects as defect_history
from qe.engines.agents.gateway import AgentRequest, LLMGateway, ReplayMiss, StaleReplay
from qe.engines.agents.prompts import prompt_version
from qe.engines.agents.schemas import CaseMapping, DefectMapping, HiddenRules, RiskCard
from qe.engines.estate import Estate
from qe.engines.ontology.ontology import grounding_for

RECORDINGS = Path(__file__).resolve().parents[1] / "agent-recordings"
AREA = "billing"
# Seed data is test data, not behaviour, and would only add reading for the agent.
NOT_BEHAVIOUR = ("Data/SeedData.cs",)

SCHEMAS: dict[str, type[BaseModel]] = {
    "coverage_mapper": CaseMapping,
    "defect_clusterer": DefectMapping,
    "hidden_rule_finder": HiddenRules,
    "risk_analyst": RiskCard,
}


@dataclass(frozen=True)
class Sources:
    estate: Estate
    faults_file: Path
    results: Path
    repo: Path
    gate_percent: int

    @classmethod
    def at(cls, qe_root: Path, repo: Path, gate_percent: int) -> "Sources":
        return cls(
            Estate(qe_root / "estate"),
            qe_root / "faults" / "faults.yaml",
            qe_root / "lab" / "results",
            repo,
            gate_percent,
        )


class CheckFailed(ValueError):
    pass


def _register(src: Sources) -> list[dict[str, Any]]:
    return [
        {"id": r["id"], "title": r["title"], "critical": r["critical"], "statement": r["statement"]}
        for r in src.estate.rules()
    ]


def _rule_ids(src: Sources) -> set[str]:
    return {rule["id"] for rule in src.estate.rules()}


def _code(src: Sources) -> dict[str, str]:
    return {
        path.relative_to(src.estate.source).as_posix(): path.read_text(encoding="utf-8")
        for path in src.estate.code_files()
        if not path.as_posix().endswith(NOT_BEHAVIOUR)
    }


def _help_pages(src: Sources) -> dict[str, str]:
    folder = src.estate.root / "docs" / "help"
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(folder.glob("*.md"))}


def _test_sources(src: Sources) -> dict[str, str]:
    return {
        path.relative_to(src.estate.tests).as_posix(): path.read_text(encoding="utf-8")
        for path in src.estate.test_files()
    }


def _grounded(material: dict[str, Any]) -> dict[str, Any]:
    return {**material, "ontology": grounding_for(json.dumps(material, default=str))}


# Requests


def mapper_request(src: Sources) -> AgentRequest:
    material = {"rules": _register(src), "manual_cases": src.estate.manual_cases()}
    return AgentRequest("coverage_mapper", AREA, prompt_version("coverage_mapper"), material)


def clusterer_request(src: Sources, found: list[defect_history.Defect]) -> AgentRequest:
    material = {
        "rules": _register(src),
        "defects": [
            {
                "id": d.id,
                "title": d.title,
                "repro": d.repro,
                "resolution": d.resolution,
                "code_files": list(d.code_files),
            }
            for d in found
        ],
    }
    return AgentRequest("defect_clusterer", AREA, prompt_version("defect_clusterer"), material)


def finder_request(src: Sources) -> AgentRequest:
    material = {
        "rules": _register(src),
        "help_pages": _help_pages(src),
        "manual_cases": src.estate.manual_cases(),
        "automated_tests": _test_sources(src),
        "code": _code(src),
    }
    return AgentRequest("hidden_rule_finder", AREA, prompt_version("hidden_rule_finder"), _grounded(material))


def risk_request(
    src: Sources, row: coverage.RuleCoverage, linked: list[defect_history.Defect]
) -> AgentRequest:
    rule = next(r for r in _register(src) if r["id"] == row.rule)
    material = {
        "rule": rule,
        "automated_tests": [test["title"] for test in row.tests],
        "defects": [
            {
                "id": d.id,
                "title": d.title,
                "severity": d.severity,
                "created": d.created,
                "repro": d.repro,
                "resolution": d.resolution,
                "tests_added": {"automated": d.test_file, "manual": "manual case updated", "none": "none"}[
                    d.test
                ],
                "fix": defect_history.fix_diff(src.repo, d.commit),
            }
            for d in linked
        ],
    }
    return AgentRequest("risk_analyst", row.rule, prompt_version("risk_analyst"), _grounded(material))


# Checks


def _check_ontology(request: AgentRequest, used: list[str]) -> None:
    given = {concept["id"] for concept in request.payload.get("ontology", [])}
    if unknown := set(used) - given:
        raise CheckFailed(f"{request.agent}: concepts not in its grounding: {sorted(unknown)}")


def _check_mapping(
    request: AgentRequest, rows: list[dict[str, Any]], key: str, id_field: str, rules: set[str]
) -> None:
    given = [str(entry["id"]) for entry in request.payload[key]]
    returned = [str(row[id_field]) for row in rows]
    if sorted(returned) != sorted(given):
        raise CheckFailed(f"{request.agent}: did not return every item exactly once")
    if bad := {row["rule"] for row in rows if row["rule"] is not None} - rules:
        raise CheckFailed(f"{request.agent}: unknown rules {sorted(bad)}")


def _resolve(code: dict[str, str], citation: dict[str, Any]) -> dict[str, Any]:
    text = code.get(citation["file"])
    if text is None:
        raise CheckFailed(f"cited file is not in the module: {citation['file']}")
    lines = [n for n, line in enumerate(text.splitlines(), start=1) if citation["find"] in line]
    if not citation["find"].strip() or not lines:
        raise CheckFailed(f"citation not found in {citation['file']}: {citation['find']}")
    return {**citation, "line": lines[0], "text": text.splitlines()[lines[0] - 1].strip()}


def document_search(src: Sources, phrases: list[str]) -> list[dict[str, Any]]:
    """Where each phrase appears in the register, help pages, manual cases and automated tests."""
    places: dict[str, str] = {f"Rule {r['id']}": r["statement"] for r in _register(src)}
    places |= {f"Help page {name}": text for name, text in _help_pages(src).items()}
    for case in src.estate.manual_cases():
        steps = " ".join(f"{s['action']} {s['expected']}" for s in case["steps"])
        places[f"Manual case {case['id']}"] = f"{case['title']} {steps}"
    places |= {f"Test {path}": text for path, text in _test_sources(src).items()}
    return [
        {
            "phrase": phrase,
            "found_in": [
                where for where, text in places.items() if re.search(re.escape(phrase), text, re.IGNORECASE)
            ],
        }
        for phrase in phrases
    ]


def checked(src: Sources, request: AgentRequest, output: dict[str, Any]) -> dict[str, Any]:
    """Every result passes the same checks, recorded or live."""
    content = SCHEMAS[request.agent].model_validate(output).model_dump()
    rules = _rule_ids(src)
    if request.agent == "coverage_mapper":
        _check_mapping(request, content["cases"], "manual_cases", "case_id", rules)
    elif request.agent == "defect_clusterer":
        _check_mapping(request, content["defects"], "defects", "defect_id", rules)
    elif request.agent == "hidden_rule_finder":
        code = request.payload["code"]
        for rule in content["rules"]:
            _check_ontology(request, rule["ontology_concepts"])
            if rule["related_rule"] is not None and rule["related_rule"] not in rules:
                raise CheckFailed(f"hidden rule names an unknown rule {rule['related_rule']}")
            if not rule["citations"]:
                raise CheckFailed(f"hidden rule has no code citation: {rule['title']}")
            rule["citations"] = [_resolve(code, citation) for citation in rule["citations"]]
            if any(len(phrase.split()) < 2 for phrase in rule["search_phrases"]):
                raise CheckFailed(f"hidden rule has a one-word search phrase: {rule['title']}")
            rule["document_search"] = document_search(src, rule["search_phrases"])
            rule["documented"] = any(hit["found_in"] for hit in rule["document_search"])
    elif request.agent == "risk_analyst":
        _check_ontology(request, content["ontology_concepts"])
        given = {d["id"] for d in request.payload["defects"]}
        cited = {i for p in content["what_keeps_breaking"] + content["proposed_tests"] for i in p["defects"]}
        if unknown := cited - given:
            raise CheckFailed(f"risk card cites defects it was not given: {sorted(unknown)}")
    return content


# The analysis


def _run(src: Sources, gateway: LLMGateway, request: AgentRequest) -> dict[str, Any]:
    try:
        result = gateway.run(request, SCHEMAS[request.agent])
    except ReplayMiss:
        return {"status": "not_run"}
    except StaleReplay:
        return {"status": "stale"}
    return {
        "status": "ok",
        "content": checked(src, request, result.output),
        "source": result.source,
        "model": result.model,
        "duration_ms": result.duration_ms,
        "input_hash": request.input_hash,
    }


def risk_ranking(
    rows: list[coverage.RuleCoverage], linked: dict[str, list[defect_history.Defect]]
) -> list[dict[str, Any]]:
    """Critical rules that are not covered come first, then the most defects with no automated test."""
    ranked = []
    for row in rows:
        members = linked.get(row.rule, [])
        files: dict[str, int] = {}
        for defect in members:
            for path in defect.code_files:
                files[path] = files.get(path, 0) + 1
        ranked.append(
            {
                "rule": row.rule,
                "title": row.title,
                "critical": row.critical,
                "covered": row.covered,
                "score": row.score,
                "defects": [d.brief() for d in members],
                "untested": sum(1 for d in members if d.test != "automated"),
                "no_test": sum(1 for d in members if d.test == "none"),
                "files": sorted(files.items(), key=lambda item: (-item[1], item[0])),
            }
        )
    return sorted(
        ranked,
        key=lambda r: (
            not (r["critical"] and not r["covered"]),
            -r["untested"],
            -len(r["defects"]),
            r["rule"],
        ),
    )


def analyse(src: Sources, gateway: LLMGateway) -> dict[str, Any]:
    rows = coverage.coverage_map(src.estate, src.faults_file, src.results, src.gate_percent)
    found = defect_history.defects(src.estate, src.repo)
    by_id = {d.id: d for d in found}
    mapping = _run(src, gateway, mapper_request(src))
    clustering = _run(src, gateway, clusterer_request(src, found))
    hidden = _run(src, gateway, finder_request(src))

    linked: dict[str, list[defect_history.Defect]] = {}
    ranking: list[dict[str, Any]] = []
    cards: dict[str, dict[str, Any]] = {}
    if clustering["status"] == "ok":
        for entry in clustering["content"]["defects"]:
            if entry["rule"]:
                linked.setdefault(entry["rule"], []).append(by_id[entry["defect_id"]])
        ranking = risk_ranking(rows, linked)
        for entry in ranking:
            if entry["critical"] and not entry["covered"] and entry["defects"]:
                row = next(r for r in rows if r.rule == entry["rule"])
                cards[entry["rule"]] = _run(src, gateway, risk_request(src, row, linked[entry["rule"]]))

    cases_by_rule: dict[str, list[str]] = {}
    if mapping["status"] == "ok":
        for case in mapping["content"]["cases"]:
            if case["rule"]:
                cases_by_rule.setdefault(case["rule"], []).append(case["case_id"])

    return {
        "coverage": [
            {
                "rule": row.rule,
                "title": row.title,
                "critical": row.critical,
                "tests": row.tests,
                "faults": row.faults,
                "caught": row.caught,
                "score": row.score,
                "covered": row.covered,
                "manual_cases": cases_by_rule.get(row.rule, []),
                "defects": [d.id for d in linked.get(row.rule, [])],
            }
            for row in rows
        ],
        "summary": coverage.summary(rows),
        "gate_percent": src.gate_percent,
        "case_mapping": mapping,
        "defect_mapping": clustering,
        "clusters": defect_history.clusters_by_code(found),
        "risk_ranking": ranking,
        "risk_cards": cards,
        "hidden_rules": hidden,
        "dead_code": deadcode.find(src.estate),
    }
