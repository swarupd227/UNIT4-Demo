"""The defect history, read from the Azure DevOps export and the module's Git repository.

Plain code only. Each defect's fix commit says which files it touched, and the export says whether
the fix added an automated test, only updated a manual case, or added nothing. Defects are grouped
by the code their fixes touched.
"""

import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from qe.engines.estate import Estate

SOURCE_PREFIX = "src/"
AUTOMATED_PREFIX = "Automated test:"


@dataclass(frozen=True)
class Defect:
    id: str
    title: str
    severity: int
    created: str
    repro: str
    resolution: str
    commit: str
    files: tuple[str, ...]
    test: str  # automated, manual or none
    test_file: str | None

    @property
    def code_files(self) -> tuple[str, ...]:
        return tuple(f for f in self.files if f.startswith(SOURCE_PREFIX))

    def brief(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "severity": self.severity, "test": self.test}


def _git(repo: Path, *args: str) -> str:
    # The repository is mounted from the host, so Git would otherwise refuse it as another user's.
    command = ["git", "-c", "safe.directory=*", "-C", str(repo), *args]
    return subprocess.run(command, capture_output=True, text=True, check=True, encoding="utf-8").stdout


def commit_files(repo: Path) -> dict[str, tuple[str, ...]]:
    """Every commit and the files it changed, from one `git log`."""
    files: dict[str, list[str]] = {}
    current = None
    for line in _git(repo, "log", "--name-only", "--format=@%H").splitlines():
        if line.startswith("@"):
            current = line[1:]
            files[current] = []
        elif line and current:
            files[current].append(line)
    return {commit: tuple(changed) for commit, changed in files.items()}


def fix_diff(repo: Path, commit: str) -> str:
    return _git(repo, "show", "--format=%s", "--unified=2", commit, "--", SOURCE_PREFIX)


def _test_kind(value: str) -> tuple[str, str | None]:
    value = value.strip()
    if value.startswith(AUTOMATED_PREFIX):
        return "automated", value.removeprefix(AUTOMATED_PREFIX).strip()
    return ("manual", None) if value else ("none", None)


def defects(estate: Estate, repo: Path) -> list[Defect]:
    changed = commit_files(repo) if repo.exists() else {}
    found = []
    for row in estate.defects():
        test, test_file = _test_kind(row["Tests Added"])
        found.append(
            Defect(
                id=f"BILL-{row['ID']}",
                title=row["Title"],
                severity=int(row["Severity"].split(" ")[0]),
                created=datetime.strptime(row["Created Date"].split(" ")[0], "%m/%d/%Y").date().isoformat(),
                repro=row["Repro Steps"],
                resolution=row["Resolution"],
                commit=row["Linked Commit"],
                files=changed.get(row["Linked Commit"], ()),
                test=test,
                test_file=test_file,
            )
        )
    return found


def clusters_by_code(found: list[Defect]) -> list[dict[str, Any]]:
    """Defects grouped by the source file their fixes touched, largest group first."""
    groups: dict[str, list[Defect]] = defaultdict(list)
    for defect in found:
        for path in defect.code_files:
            groups[path].append(defect)
    return sorted(
        (
            {
                "file": path,
                "defects": len(members),
                "no_test": sum(1 for d in members if d.test == "none"),
                "manual_only": sum(1 for d in members if d.test == "manual"),
                "automated": sum(1 for d in members if d.test == "automated"),
            }
            for path, members in groups.items()
        ),
        key=lambda group: (-group["defects"], group["file"]),
    )
