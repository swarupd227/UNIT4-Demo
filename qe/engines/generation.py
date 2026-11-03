"""Turns manual cases, defects and approved context into Playwright tests, and judges each one.

Plain code does the intake (duplicates and cases an existing test already covers), hands each source
to the generator with only the data no other test owns, and checks every candidate four ways:

1. Conventions: it follows the suite's conventions (qe.engines.conventions).
2. Independent expected results: a validator agent that never sees the test works out what each
   asserted value should be from the documents, and every value must agree.
3. Seeded faults: in the lab it catches its rule's faults, and a defect's test catches the fault that
   puts that defect back. A catch is a failure on five fresh databases.
4. Stability: it passes 20 runs of the whole suite, each on a fresh database.

Only a candidate that passes all four is put to an engineer.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from qe.engines import conventions
from qe.engines import defects as defect_history
from qe.engines.agents.gateway import AgentRequest
from qe.engines.agents.prompts import prompt_version
from qe.engines.agents.schemas import CaseReview, GeneratedTest, TestValidation
from qe.engines.analysis import CheckFailed, Sources

QE_ROOT = Path(__file__).resolve().parents[1]
GENERATED = QE_ROOT / "generated"
BATCH = QE_ROOT / "generation" / "batch.yaml"
PROOF = QE_ROOT / "lab" / "results" / "proof"
STABLE_RUNS = 20
PROJECT_LABEL = re.compile(r'Select Project "(P-\d{4} [^"]+)"')
MARKUP = (
    "Proposals/Create.cshtml",
    "Proposals/Edit.cshtml",
    "Invoices/Details.cshtml",
    "Shared/_Layout.cshtml",
)
EXAMPLES = ("pricing/proposal-totals.spec.ts", "proposals/write-up.spec.ts", "invoicing/credit-notes.spec.ts")


@dataclass(frozen=True)
class Material:
    src: Sources
    analysis: dict[str, Any]

    @property
    def tests(self) -> Path:
        return self.src.estate.tests

    def rule(self, rule_id: str) -> dict[str, Any]:
        return next(r for r in self.src.estate.rules() if r["id"] == rule_id)

    def catalogue(self) -> str:
        return (self.src.estate.root / "test-data" / "catalogue.yaml").read_text(encoding="utf-8")

    def projects(self) -> dict[str, dict[str, Any]]:
        return yaml.safe_load(self.catalogue())["projects"]

    def documents(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        rules = yaml.safe_dump({"rules": self.src.estate.rules()}, sort_keys=False, width=110)
        docs = {"Rule register": rules, "Test data catalogue": self.catalogue()}
        folder = self.src.estate.root / "docs" / "help"
        docs |= {f"Help page {p.name}": p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.md"))}
        return docs | (extra or {})

    def case_rules(self) -> dict[str, str | None]:
        return {c["case_id"]: c["rule"] for c in self.analysis["case_mapping"]["content"]["cases"]}

    def hidden_rule(self, entry_id: str) -> dict[str, Any]:
        number = int(entry_id.split("-")[1])
        return dict(self.analysis["hidden_rules"]["content"]["rules"][number - 1])


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plain(text: str) -> str:
    """A quote as written, without the escaping or spacing a model may add around it."""
    return re.sub(r"\s+", " ", text.replace('\\"', '"').replace("\\'", "'")).strip()


def _resolve_basis(documents: dict[str, str], basis: list[dict[str, Any]], where: str) -> None:
    for item in basis:
        text = documents.get(item["document"])
        if text is None:
            raise CheckFailed(f"{where}: cites a document it was not given: {item['document']}")
        quote = _plain(item["find"])
        if not quote or not any(quote in _plain(line) for line in text.splitlines()):
            raise CheckFailed(f"{where}: quote not found in {item['document']}: {item['find']}")


# Intake


def _steps_key(case: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple((s["action"].strip(), s["expected"].strip()) for s in case["steps"])


def intake(material: Material) -> list[dict[str, Any]]:
    """What happens to each manual case in the batch before any agent reads it."""
    batch = yaml.safe_load(BATCH.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in material.src.estate.manual_cases()}
    rules = material.case_rules()
    suite = conventions.read_suite(material.src.estate)
    labels = {f"{g}.{k}": v for g, keys in suite.data_keys.items() for k, v in keys.items()}
    first_with_steps: dict[tuple[tuple[str, str], ...], str] = {}
    for case_id in sorted(cases):
        first_with_steps.setdefault(_steps_key(cases[case_id]), case_id)
    out = []
    for case_id in map(str, batch["manual_cases"]):
        case = cases[case_id]
        entry = {"case": case_id, "title": case["title"], "rule": rules.get(case_id)}
        original = first_with_steps[_steps_key(case)]
        duplicates = sorted(
            c for c, k in ((c, _steps_key(v)) for c, v in cases.items()) if k == _steps_key(case)
        )
        project = next((m.group(1) for s in case["steps"] if (m := PROJECT_LABEL.search(s["action"]))), None)
        owner = next(
            (suite.data_in_use[k] for k, v in labels.items() if v == project and k in suite.data_in_use), None
        )
        if original != case_id:
            entry |= {"outcome": "merged", "into": original, "duplicates": duplicates}
        elif owner and _rule_of_spec(material, owner) == entry["rule"]:
            entry |= {"outcome": "already_automated", "by": owner, "duplicates": duplicates}
        else:
            entry |= {"outcome": "review", "duplicates": duplicates}
        out.append(entry)
    return out


def _rule_of_spec(material: Material, spec: str) -> str | None:
    match = conventions.TITLE.search(_text(material.tests / spec))
    return match.group("title").split(" ")[0] if match else None


def case_request(material: Material, case_id: str) -> AgentRequest:
    case = next(c for c in material.src.estate.manual_cases() if c["id"] == case_id)
    rule = material.case_rules()[case_id]
    payload = {
        "rule": material.rule(rule) if rule else None,
        "case": {
            "id": case_id,
            "title": case["title"],
            "steps": [{"step": n, **s} for n, s in enumerate(case["steps"], start=1)],
        },
        "documents": material.documents(),
    }
    return AgentRequest("case_validator", case_id, prompt_version("case_validator"), payload)


def checked_review(request: AgentRequest, output: dict[str, Any]) -> dict[str, Any]:
    review = CaseReview.model_validate(output).model_dump()
    steps = [s["step"] for s in request.payload["case"]["steps"]]
    if sorted(s["step"] for s in review["steps"]) != steps:
        raise CheckFailed(f"case_validator on {request.subject}: did not review every step exactly once")
    for step in review["steps"]:
        _resolve_basis(request.payload["documents"], step["basis"], f"case_validator on {request.subject}")
    verdicts = {s["verdict"] for s in review["steps"]}
    # A case with a result nobody can check goes back to its author first, who restates the whole case.
    review["outcome"] = (
        "needs_expected_result"
        if "not_checkable" in verdicts
        else "to_person"
        if "disagrees" in verdicts
        else "ready"
    )
    return review


# Generation


def sources(material: Material, ready_cases: list[str]) -> list[dict[str, Any]]:
    """Every source the generator works from, in the order the batch lists them."""
    batch = yaml.safe_load(BATCH.read_text(encoding="utf-8"))
    rules = material.case_rules()
    found = {d.id: d for d in defect_history.defects(material.src.estate, material.src.repo)}
    links = {d["defect_id"]: d["rule"] for d in material.analysis["defect_mapping"]["content"]["defects"]}
    out: list[dict[str, Any]] = []
    for case_id in ready_cases:
        out.append({"id": f"MC-{case_id}", "kind": "manual_case", "ref": case_id, "rule": rules[case_id]})
    for defect_id in batch["defects"]:
        rule = links[defect_id]
        proposals = [
            t
            for t in material.analysis["risk_cards"][rule]["content"]["proposed_tests"]
            if defect_id in t["defects"]
        ]
        out.append(
            {
                "id": f"DF-{defect_id}",
                "kind": "defect",
                "ref": defect_id,
                "rule": rule,
                "defect": found[defect_id],
                "proposals": proposals,
            }
        )
    for entry_id in batch["context"]:
        hidden = material.hidden_rule(entry_id)
        out.append(
            {"id": f"CX-{entry_id}", "kind": "hidden_rule", "ref": entry_id, "rule": hidden["related_rule"]}
        )
    return out


def _source_for_generator(material: Material, source: dict[str, Any]) -> dict[str, Any]:
    if source["kind"] == "manual_case":
        case = next(c for c in material.src.estate.manual_cases() if c["id"] == source["ref"])
        return {"kind": "manual test case", "id": case["id"], "title": case["title"], "steps": case["steps"]}
    if source["kind"] == "defect":
        d: defect_history.Defect = source["defect"]
        return {
            "kind": "defect fixed without an automated test",
            "id": d.id,
            "title": d.title,
            "repro": d.repro,
            "resolution": d.resolution,
            "fix": defect_history.fix_diff(material.src.repo, d.commit),
            "risk_card_proposals": source["proposals"],
        }
    hidden = material.hidden_rule(source["ref"])
    return {
        "kind": "approved hidden rule",
        "id": source["ref"],
        "title": hidden["title"],
        "statement": hidden["statement"],
        "code": [f"{c['file']}:{c['line']}: {c['text']}" for c in hidden["citations"]],
        "proposed_test": hidden["proposed_test"],
    }


def _source_for_validator(material: Material, source: dict[str, Any]) -> dict[str, Any]:
    """The same source with every expected result taken out, so the validator works them out itself."""
    full = _source_for_generator(material, source)
    if source["kind"] == "manual_case":
        return {**full, "steps": [s["action"] for s in full["steps"]]}
    if source["kind"] == "defect":
        return {k: v for k, v in full.items() if k not in ("fix", "risk_card_proposals")}
    return {k: v for k, v in full.items() if k not in ("proposed_test",)}


def _context_document(material: Material, source: dict[str, Any]) -> dict[str, str]:
    if source["kind"] != "hidden_rule":
        return {}
    hidden = material.hidden_rule(source["ref"])
    lines = [hidden["statement"], *(f"{c['file']}:{c['line']}: {c['text']}" for c in hidden["citations"])]
    return {f"Approved context {source['ref']}": "\n".join(lines)}


def free_data(material: Material, others: set[str]) -> list[str]:
    """Projects no existing test and no other candidate uses. `others` holds the candidates' labels."""
    suite = conventions.read_suite(material.src.estate)
    used_labels = {suite.data_keys[g][k] for g, k in (key.split(".") for key in suite.data_in_use)} | others
    return [
        f"{code} {p['name']}"
        for code, p in material.projects().items()
        if not p["on_hold"] and f"{code} {p['name']}" not in used_labels
    ]


def generator_request(
    material: Material,
    source: dict[str, Any],
    attempt: int,
    others: set[str],
    previous: dict[str, Any] | None,
) -> AgentRequest:
    tests = material.tests
    pages = material.src.estate.source / "Billing.Web" / "Pages"
    payload = {
        "conventions": conventions.read_suite(material.src.estate).summary(),
        "page_objects": {p.name: _text(p) for p in sorted((tests / "pages").glob("*.ts"))},
        "fixtures": {p.name: _text(p) for p in sorted((tests / "fixtures").glob("*.ts"))},
        "examples": {name: _text(tests / "specs" / name) for name in EXAMPLES},
        "page_markup": {name: _text(pages / name) for name in MARKUP},
        "rule": material.rule(source["rule"]),
        "source": _source_for_generator(material, source),
        "test_data_catalogue": material.catalogue(),
        "free_data": free_data(material, others),
        "previous_attempt": previous,
    }
    return AgentRequest(
        "test_generator", f"{source['id']}-a{attempt}", prompt_version("test_generator"), payload
    )


def validator_request(
    material: Material, source: dict[str, Any], attempt: int, generated: dict[str, Any]
) -> AgentRequest:
    payload = {
        "rule": material.rule(source["rule"]),
        "source": _source_for_validator(material, source),
        "scenario": generated["scenario"],
        "checks": [c["check"] for c in generated["checks"]],
        "documents": material.documents(_context_document(material, source)),
    }
    return AgentRequest(
        "test_validator", f"{source['id']}-a{attempt}", prompt_version("test_validator"), payload
    )


def normalised(value: str) -> str:
    value = value.replace("\\'", "'").replace("−", "-").replace("’", "'")
    value = value.strip().strip("'\"").rstrip(".").strip()
    value = re.sub(r"(?<=\d),(?=\d{3}\b)", "", value)
    return re.sub(r"\s+", " ", value).lower()


def stated(expected: str) -> str:
    """The value the validator gives, without the working it adds in brackets after it."""
    return re.sub(r"\s*\((?:[^()]|\([^()]*\))*\)\s*$", "", expected.strip())


def agree(asserted: str, expected: str) -> bool:
    """The validator states the value first and may explain it after, in brackets or a new sentence."""
    a, e = normalised(asserted), normalised(stated(expected))
    if e.startswith(("not settled", "partly settled")):
        return False
    if e.startswith(a):
        rest = e[len(a) :]
        if not rest or rest[0] in " ,;(" or (rest[0] == "." and not rest[1:2].isdigit()):
            return True
    # A figure restated with its label, such as "Subtotal 1,920.00 and Total 1,920.00 EUR".
    if re.search(r"\d", a) and len(a) >= 4:
        return re.search(rf"(?<![\w.,-]){re.escape(a)}(?![\w-]|[.,]\d)", e) is not None
    return False


def check_generated(
    material: Material,
    source: dict[str, Any],
    generated: dict[str, Any],
    other_keys: dict[str, str],
    others: set[str],
) -> list[str]:
    """Check 1 and the plain part of 2: conventions, and that the declared values are the real ones.

    `other_keys` maps the other candidates' testData keys to their files, `others` their data labels.
    """
    suite = conventions.read_suite(material.src.estate)
    key = f"{generated['data']['group']}.{generated['data']['key']}"
    taken = dict(suite.data_in_use) | other_keys
    issues = conventions.check(
        suite, material.rule(source["rule"]), generated["path"], generated["code"], key, taken
    )
    existing = {p.relative_to(material.tests).as_posix() for p in material.src.estate.test_files()}
    if generated["path"] in existing or generated["path"] in set(other_keys.values()):
        issues.append(f"{generated['path']} is already another test's file; one file holds one test.")
    if key in {f"{g}.{k}" for g, keys in suite.data_keys.items() for k in keys}:
        issues.append(f"{key} already exists in fixtures/testData; choose a new name.")
    if generated["data"]["group"] == "projects" and generated["data"]["value"] not in free_data(
        material, others
    ):
        issues.append(f"Uses {generated['data']['value']}, which is not free test data.")
    scenario = " ".join(generated["scenario"])
    for check in generated["checks"]:
        if check["value"] not in generated["code"]:
            issues.append(
                f"Declares '{check['value']}' for {check['check']}, but the code does not assert it."
            )
        # An amount the test expects must be worked out, not read from the scenario. Counts and dates are
        # inputs the scenario may name.
        if re.search(r"\d[.,]\d", check["value"]) and check["value"] in scenario:
            issues.append(f"The scenario gives away the expected value '{check['value']}'.")
    if not generated["checks"]:
        issues.append("Asserts nothing.")
    return issues


def compare(generated: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    expected = {c["check"]: c for c in validation["checks"]}
    if set(expected) != {c["check"] for c in generated["checks"]}:
        raise CheckFailed("test_validator did not return every check exactly once")
    return [
        {
            "check": c["check"],
            "asserted": c["value"],
            "expected": expected[c["check"]]["expected"],
            "basis": expected[c["check"]]["basis"],
            "agrees": agree(c["value"], expected[c["check"]]["expected"]),
        }
        for c in generated["checks"]
    ]


def checked_validation(request: AgentRequest, output: dict[str, Any]) -> dict[str, Any]:
    validation = TestValidation.model_validate(output).model_dump()
    if sorted(c["check"] for c in validation["checks"]) != sorted(request.payload["checks"]):
        raise CheckFailed(f"test_validator on {request.subject}: did not return every check exactly once")
    for check in validation["checks"]:
        _resolve_basis(request.payload["documents"], check["basis"], f"test_validator on {request.subject}")
    return validation


def checked_generation(output: dict[str, Any]) -> dict[str, Any]:
    return GeneratedTest.model_validate(output).model_dump()


# Candidate files for the lab


def test_data_with(material: Material, additions: list[dict[str, str]]) -> str:
    text = _text(material.tests / "fixtures" / "testData.ts")
    for addition in additions:
        group, key, value = addition["group"], addition["key"], addition["value"]
        pattern = re.compile(rf"(export const {group} = \{{.*?)(\n\}};)", re.DOTALL)
        entry = f"\n  {key}: '{value}',"
        text = pattern.sub(lambda m, entry=entry: m.group(1) + entry + m.group(2), text, count=1)
    return text


def write_overlay(material: Material, attempt: int, candidates: list[dict[str, Any]]) -> Path:
    folder = GENERATED / f"attempt-{attempt}"
    ready = [c for c in candidates if c.get("ready_for_lab")]
    for c in ready:
        path = folder / c["generated"]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(c["generated"]["code"].rstrip() + "\n", encoding="utf-8", newline="\n")
    fixtures = folder / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    data = test_data_with(material, [c["generated"]["data"] for c in ready])
    (fixtures / "testData.ts").write_text(data, encoding="utf-8", newline="\n")
    return folder


# Proof


def _runs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def proof(attempt: int, faults_file: Path) -> dict[str, dict[str, Any]]:
    """Checks 3 and 4 for every candidate the lab ran in this attempt, keyed by test title."""
    faults = yaml.safe_load(faults_file.read_text(encoding="utf-8"))["faults"]
    runs = _runs(PROOF / f"attempt-{attempt}-runs.jsonl")
    fault_runs = _runs(PROOF / f"attempt-{attempt}-faults.jsonl")
    passed: dict[str, int] = defaultdict(int)
    failures: dict[str, list[str]] = defaultdict(list)
    for run in runs:
        for test in run["tests"]:
            if test["status"] == "passed":
                passed[test["title"]] += 1
            else:
                failures[test["title"]].append(test["error"] or test["status"])
    caught: dict[str, set[str]] = defaultdict(set)
    for run in fault_runs:
        for test in run["tests"]:
            if test["status"] == "failed":
                caught[test["title"]].add(run["build"])
    titles = {t["title"] for run in runs + fault_runs for t in run["tests"]}
    return {
        title: {
            "runs": len(runs),
            "passed": passed[title],
            "first_failure": failures[title][0] if failures[title] else None,
            "caught": sorted(caught[title]),
            "fault_builds": sorted({run["build"] for run in fault_runs}),
            "faults": faults,
        }
        for title in titles
    }


def judge(candidate: dict[str, Any], lab: dict[str, Any] | None) -> dict[str, Any]:
    """The four checks for one candidate, and the problems to give the generator if it fails."""
    rule = candidate["rule"]
    disagreements = [v for v in candidate.get("validation", []) if not v["agrees"]]
    checks: dict[str, Any] = {
        "conventions": {"passed": not candidate["issues"], "issues": candidate["issues"]},
        "expected_results": {
            "passed": bool(candidate.get("validation")) and not disagreements,
            "disagreements": disagreements,
        },
    }
    problems = list(candidate["issues"]) + [
        f"{v['check']}: the test asserts '{v['asserted']}', but the documents give '{v['expected']}'."
        for v in disagreements
    ]
    if lab is None:
        checks["faults"] = {"passed": False, "ran": False}
        checks["stability"] = {"passed": False, "ran": False}
        if candidate.get("ready_for_lab"):
            problems.append(
                "The lab found no result for this test. Check that the file compiles and the title is unique."
            )
    else:
        rule_faults = [f for f in lab["faults"] if f["rule"] == rule]
        target = [
            f for f in rule_faults if candidate["kind"] == "defect" and f.get("defect") == candidate["ref"]
        ]
        needed = target or rule_faults
        caught = [f["id"] for f in rule_faults if f["id"] in lab["caught"]]
        missed = [f for f in needed if f["id"] not in lab["caught"]]
        faults_ok = bool(caught) and (not target or not missed)
        checks["faults"] = {
            "passed": faults_ok,
            "ran": True,
            "rule_faults": [f["id"] for f in rule_faults],
            "caught": caught,
            "required": [f["id"] for f in target],
        }
        stable = lab["runs"] >= STABLE_RUNS and lab["passed"] == lab["runs"]
        checks["stability"] = {
            "passed": stable,
            "ran": True,
            "passed_runs": lab["passed"],
            "runs": lab["runs"],
            "first_failure": lab["first_failure"],
        }
        if not stable:
            problems.append(
                f"The test failed in {lab['runs'] - lab['passed']} of {lab['runs']} runs of the unchanged "
                f"module. First failure: {lab['first_failure']}"
            )
        if not faults_ok:
            for fault in missed or needed:
                problems.append(
                    f"The test still passed on a build where this was broken: {fault['description']}. "
                    "Choose data and checks on which that change shows."
                )
    accepted = all(check["passed"] for check in checks.values())
    return {"checks": checks, "accepted": accepted, "problems": [] if accepted else problems}


def previous_attempt(
    candidate: dict[str, Any], verdict: dict[str, Any], files_in_use: list[str]
) -> dict[str, Any]:
    generated = candidate["generated"]
    problems = [*verdict["problems"], f"Files already in use: {', '.join(sorted(files_in_use))}."]
    return {
        "data": generated["data"],
        "scenario": generated["scenario"],
        "checks": generated["checks"],
        "code": generated["code"],
        "problems": problems,
    }


def manifest_path(attempt: int) -> Path:
    return GENERATED / f"attempt-{attempt}" / "manifest.json"


def load_manifest(attempt: int) -> dict[str, Any] | None:
    path = manifest_path(attempt)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def attempts() -> list[int]:
    return sorted(int(p.parent.name.split("-")[1]) for p in GENERATED.glob("attempt-*/manifest.json"))


# What the workbench shows


def history() -> dict[str, list[dict[str, Any]]]:
    """Every attempt at every candidate, oldest first, each with its four checks."""
    faults_file = QE_ROOT / "faults" / "faults.yaml"
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt in attempts():
        manifest = load_manifest(attempt)
        assert manifest is not None
        lab = proof(attempt, faults_file)
        for candidate in manifest["candidates"]:
            if candidate["attempt"] != attempt:
                continue
            ran = lab.get(candidate["title"]) if candidate["ready_for_lab"] else None
            out[candidate["id"]].append({**candidate, **judge(candidate, ran)})
    return dict(out)


def coverage_after(
    coverage: list[dict[str, Any]], accepted: list[dict[str, Any]], gate: int
) -> dict[str, Any]:
    """The coverage map again, with the accepted tests' catches added to the existing tests'."""
    caught_by_new: dict[str, set[str]] = defaultdict(set)
    for candidate in accepted:
        caught_by_new[candidate["rule"]] |= set(candidate["checks"]["faults"]["caught"])
    rows = []
    for row in coverage:
        caught = {f["id"] for f in row["faults"] if f["caught"]} | caught_by_new[row["rule"]]
        tests = len(row["tests"]) + sum(1 for c in accepted if c["rule"] == row["rule"])
        score = round(100 * len(caught) / len(row["faults"])) if row["faults"] else None
        rows.append(
            {
                "rule": row["rule"],
                "title": row["title"],
                "critical": row["critical"],
                "tests": tests,
                "caught": len(caught),
                "faults": len(row["faults"]),
                "score_before": row["score"],
                "score": score,
                "covered_before": row["covered"],
                "covered": tests > 0 and score is not None and score >= gate,
            }
        )
    critical = [r for r in rows if r["critical"]]
    covered = [r["rule"] for r in critical if r["covered"]]
    return {
        "rules": rows,
        "critical_covered": len(covered),
        "critical_rules": len(critical),
        "percent": round(100 * len(covered) / len(critical)) if critical else 0,
        "newly_covered": [r["rule"] for r in critical if r["covered"] and not r["covered_before"]],
    }
