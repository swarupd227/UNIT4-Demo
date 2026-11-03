"""The conventions of the existing Playwright suite, read from its files, and the check that a new
test follows them.

Plain code only. The conventions are what the 12 existing tests already do: the fixture and data
imports, the page objects, how titles name the rule, where files live and which seeded data each test
owns. They stand in for Full Circuit's own conventions, which are a discovery item.
"""

import re
from dataclasses import dataclass
from typing import Any

from qe.engines.estate import Estate

AREAS = ("invoicing", "pricing", "proposals")
FIXTURE_IMPORT = "import { expect, test } from '../../fixtures/billing';"
DATA_IMPORT = re.compile(r"import \{[^}]+\} from '\.\./\.\./fixtures/testData';")
DATA_KEY = re.compile(r"\b(projects|customers|invoices)\.(\w+)")
TITLE = re.compile(r"""^\s*test\(\s*(['"`])(?P<title>(?:\\.|(?!\1).)+?)\1""", re.MULTILINE)
PAGE_OBJECT = re.compile(r"export class (\w+)")
METHOD = re.compile(r"^\s{2}(?:async\s+)?(?:get\s+)?(\w+)\(", re.MULTILINE)
FORBIDDEN = {
    r"waitForTimeout\(": "Waits a fixed time instead of waiting for the page.",
    r"https?://": "Uses an absolute address instead of the configured base URL.",
    r"\btest\.only\(": "Leaves test.only in place.",
    r"\btest\.skip\(": "Skips itself.",
    r"\.serial\(|mode: 'serial'": "Depends on running in a fixed order.",
}
FILE_NAME = re.compile(r"^specs/(invoicing|pricing|proposals)/[a-z0-9]+(-[a-z0-9]+)*\.spec\.ts$")


@dataclass(frozen=True)
class Suite:
    page_objects: dict[str, list[str]]
    data_in_use: dict[str, str]  # testData key -> the spec that uses it
    data_keys: dict[str, dict[str, str]]  # testData group -> key -> value

    def summary(self) -> list[str]:
        objects = ", ".join(f"{name} ({len(methods)})" for name, methods in self.page_objects.items())
        return [
            f"Tests import test and expect from fixtures/billing, which hands each test its page objects: {objects}.",  # noqa: E501
            "Seeded data is named in fixtures/testData and never typed into a test.",
            "A title starts with the rule it proves, then says the behaviour in plain words; critical rules end with @critical.",  # noqa: E501
            f"Files live in specs/{{{','.join(AREAS)}}}/ and are named in kebab case.",
            "Each test owns its seeded project or invoice, so tests can run in parallel without touching each other's data.",  # noqa: E501
            "Tests wait for the page, never for a fixed time.",
        ]


def _test_data(estate: Estate) -> dict[str, dict[str, str]]:
    text = (estate.tests / "fixtures" / "testData.ts").read_text(encoding="utf-8")
    groups: dict[str, dict[str, str]] = {}
    for group, body in re.findall(r"export const (\w+) = \{(.*?)\n\};", text, re.DOTALL):
        groups[group] = dict(re.findall(r"^\s+(\w+): '([^']+)'", body, re.MULTILINE))
    return groups


def read_suite(estate: Estate) -> Suite:
    objects = {}
    for path in sorted((estate.tests / "pages").glob("*.ts")):
        text = path.read_text(encoding="utf-8")
        name = PAGE_OBJECT.search(text)
        if name:
            objects[name.group(1)] = [m for m in METHOD.findall(text) if m != "constructor"]
    in_use = {}
    for path in estate.test_files():
        for group, key in DATA_KEY.findall(path.read_text(encoding="utf-8")):
            in_use[f"{group}.{key}"] = path.relative_to(estate.tests).as_posix()
    return Suite(objects, in_use, _test_data(estate))


def check(
    suite: Suite,
    rule: dict[str, Any],
    path: str,
    code: str,
    data_key: str,
    taken: dict[str, str],
) -> list[str]:
    """Every way the candidate breaks a convention. An empty list means it follows them all."""
    issues = []
    if not FILE_NAME.match(path):
        issues.append(f"File {path} is not under specs/<area>/ with a kebab-case .spec.ts name.")
    if FIXTURE_IMPORT not in code:
        issues.append("Does not import test and expect from fixtures/billing.")
    if not DATA_IMPORT.search(code):
        issues.append("Does not take its data from fixtures/testData.")
    titles = [m.group("title") for m in TITLE.finditer(code)]
    if len(titles) != 1:
        issues.append(f"Has {len(titles)} tests; one test per file proves one behaviour.")
    else:
        title = titles[0]
        if not title.startswith(f"{rule['id']} "):
            issues.append(f"Title does not start with {rule['id']}.")
        if rule["critical"] != title.endswith(" @critical"):
            issues.append("Title must end with @critical exactly when the rule is critical.")
    for pattern, reason in FORBIDDEN.items():
        if re.search(pattern, code):
            issues.append(reason)
    used = {f"{g}.{k}" for g, k in DATA_KEY.findall(code)}
    if data_key not in used:
        issues.append(f"Does not use its own data, {data_key}.")
    for key in sorted(used):
        if key in taken:
            issues.append(f"Uses {key}, which {taken[key]} already uses.")
    return issues
