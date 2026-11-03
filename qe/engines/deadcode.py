"""Code no user can reach, found by plain code rather than an agent's opinion.

Every page is a route, so the pages and Program.cs are where users and the host enter. A type is
reachable when a reachable file names it. A static helper method is unreachable when only
unreachable files call it. Names are matched as whole words, which is enough for this module; a
pilot on a larger code base would use the compiler's own symbol graph (Roslyn) instead.
"""

import re
from dataclasses import dataclass
from typing import Any

from qe.engines.estate import Estate

TYPE_PATTERN = re.compile(r"\b(?:class|record|enum|interface|struct)\s+([A-Z]\w*)")
STATIC_CLASS_PATTERN = re.compile(r"\bstatic\s+class\s+([A-Z]\w*)")
STATIC_METHOD_PATTERN = re.compile(r"public\s+static\s+(?!class\b)[\w<>\[\],.? ]+?\s+([A-Z]\w*)\s*\(")
NAME_PATTERN = re.compile(r"\b[A-Z]\w*\b")
ROOTS = ("Pages/", "Program.cs")


@dataclass(frozen=True)
class SourceFile:
    path: str
    text: str


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _files(estate: Estate) -> list[SourceFile]:
    return [
        SourceFile(p.relative_to(estate.source).as_posix(), p.read_text(encoding="utf-8"))
        for p in estate.code_files()
    ]


def _is_root(source: SourceFile) -> bool:
    relative = source.path.split("/", 1)[1] if "/" in source.path else source.path
    return relative.startswith(ROOTS)


def reachable_files(files: list[SourceFile]) -> set[str]:
    declared: dict[str, set[str]] = {}
    for source in files:
        for name in TYPE_PATTERN.findall(source.text):
            declared.setdefault(name, set()).add(source.path)
    by_path = {source.path: source for source in files}
    reached = {source.path for source in files if _is_root(source)}
    queue = list(reached)
    while queue:
        names = set(NAME_PATTERN.findall(by_path[queue.pop()].text))
        for name in names & declared.keys():
            for path in declared[name] - reached:
                reached.add(path)
                queue.append(path)
    return reached


def find(estate: Estate) -> list[dict[str, Any]]:
    files = _files(estate)
    reached = reachable_files(files)
    found: list[dict[str, Any]] = []
    for source in files:
        if source.path in reached:
            continue
        for match in TYPE_PATTERN.finditer(source.text):
            found.append(
                {
                    "kind": "class",
                    "name": match.group(1),
                    "file": source.path,
                    "line": _line_of(source.text, match.start()),
                    "reason": "No page, service registration or reachable code refers to it.",
                    "called_from": [],
                }
            )
    for source in files:
        if source.path not in reached or not STATIC_CLASS_PATTERN.search(source.text):
            continue
        owner = STATIC_CLASS_PATTERN.search(source.text).group(1)  # type: ignore[union-attr]
        for match in STATIC_METHOD_PATTERN.finditer(source.text):
            name = match.group(1)
            call = re.compile(rf"\b{name}\s*\(")
            callers = {
                other.path
                for other in files
                if len(call.findall(other.text)) > (1 if other.path == source.path else 0)
            }
            if callers & reached:
                continue
            found.append(
                {
                    "kind": "method",
                    "name": f"{owner}.{name}",
                    "file": source.path,
                    "line": _line_of(source.text, match.start()),
                    "reason": (
                        "Called only from code no user can reach." if callers else "Nothing calls it."
                    ),
                    "called_from": sorted(callers),
                }
            )
    return found
