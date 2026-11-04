"""The pull request that brings the accepted tests and the flaky-test fixes into the module's repository.

Plain code only. The pull request is real Git: an engineer approves or rejects each item, and the merge
commits only the approved ones on a branch and merges it into main. It changes only the test suite, so
the pipeline and its release stage are untouched, and plain code checks that before the merge.
"""

import copy
import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from qe.engines import generation, maintenance

PR_ID = "PR-1"
BRANCH = "qe/billing-tests"
TESTS = "tests/e2e/"
PIPELINE = "azure-pipelines.yml"
# Fictional addresses for the commits in the module's own repository.
AGENT_AUTHOR = ("Test Assurance agents", "test-assurance@kestrel.example")
REVIEWER_EMAIL = "{key}@kestrel.example"


class MissingRepository(RuntimeError):
    pass


class GitFailed(RuntimeError):
    pass


def _git(repo: Path, *args: str, author: tuple[str, str] | None = None) -> str:
    # Without its own .git, Git would walk up and act on whatever repository holds this folder.
    if not (repo / ".git").is_dir():
        raise MissingRepository(
            f"The module repository at {repo} is missing. Reset the workbench to rebuild it."
        )
    who = author or AGENT_AUTHOR
    command = [
        "git", "-c", "safe.directory=*", "-c", f"user.name={who[0]}", "-c", f"user.email={who[1]}",
        "-C", str(repo), *args,
    ]  # fmt: skip
    done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise GitFailed(f"git {args[0]} failed: {done.stderr.strip() or done.stdout.strip()}")
    return done.stdout


def suite_folder() -> Path:
    """The suite after generation and the flaky-test fixes, laid out like tests/e2e."""
    return maintenance.OUT / "flaky-fix"


def _in_repo(repo: Path, path: str) -> str | None:
    try:
        return _git(repo, "show", f"main:{path}")
    except GitFailed:
        return None


def _runs_by_title() -> dict[str, list[dict[str, Any]]]:
    path = maintenance.RESULTS / "flaky-fix-runs.jsonl"
    record: dict[str, list[dict[str, Any]]] = {}
    if not path.exists():
        return record
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            for test in json.loads(line)["tests"]:
                record.setdefault(test["title"], []).append(
                    {"status": test["status"], "ms": test["durationMs"], "started": test.get("started")}
                )
    return record


def items() -> list[dict[str, Any]]:
    """Every test and fix in the pull request, with the evidence an engineer needs to decide."""
    key = generation.version(
        (generation.GENERATED, "attempt-*/manifest.json"),
        (generation.PROOF, "*.jsonl"),
        (maintenance.OUT, "*.json"),
        (maintenance.RESULTS, "*.jsonl"),
    )
    return copy.deepcopy(_items(key))


@lru_cache(maxsize=1)
def _items(_version: tuple[Any, ...]) -> list[dict[str, Any]]:
    runs = _runs_by_title()
    out = []
    for entries in generation.history().values():
        last = entries[-1]
        if not last["accepted"]:
            continue
        out.append(
            {
                "item_id": last["id"],
                "kind": "test",
                "title": last["title"],
                "rule": last["rule"],
                "source": {"kind": last["kind"], "ref": last["ref"]},
                "files": [TESTS + last["generated"]["path"]],
                "data": last["generated"]["data"],
                "attempts": len(entries),
                "validation": last["validation"],
                "faults": last["checks"]["faults"],
                "conventions": last["checks"]["conventions"],
                "runs": runs.get(last["title"], []),
                "agents": last["agents"],
            }
        )
    flaky = maintenance.load("flaky") or {"diagnoses": []}
    for entry in flaky["diagnoses"]:
        title = entry["test"]["title"]
        out.append(
            {
                "item_id": f"FLAKY-{entry['test']['rule']}",
                "kind": "flaky_fix",
                "title": title,
                "rule": entry["test"]["rule"],
                "source": {"kind": "flaky", "ref": entry["test"]["file"]},
                "files": [TESTS + f["path"] for f in entry["diagnosis"]["files"]],
                "cause": entry["diagnosis"]["cause"],
                "fix_summary": entry["diagnosis"]["fix_summary"],
                "before": {"failed": entry["test"]["failed"], "runs": entry["test"]["runs"]},
                "runs": runs.get(title, []),
                "agents": {"diagnoser": entry["agent"]},
            }
        )
    return out


def _main_commit(repo: Path) -> str:
    ref = repo / ".git" / "refs" / "heads" / "main"
    return (
        ref.read_text(encoding="utf-8").strip() if ref.exists() else _git(repo, "rev-parse", "main").strip()
    )


def changed_files(repo: Path) -> list[dict[str, Any]]:
    """The files the pull request adds or changes, against the repository's main branch."""
    key = (str(repo), _main_commit(repo), generation.version((suite_folder(), "**/*")))
    return copy.deepcopy(_changed_files(key))


@lru_cache(maxsize=1)
def _changed_files(key: tuple[Any, ...]) -> list[dict[str, Any]]:
    repo = Path(key[0])
    folder = suite_folder()
    out = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        repo_path = TESTS + path.relative_to(folder).as_posix()
        content = path.read_text(encoding="utf-8")
        before = _in_repo(repo, repo_path)
        if before is None or before.replace("\r\n", "\n").rstrip() != content.replace("\r\n", "\n").rstrip():
            out.append(
                {"path": repo_path, "status": "added" if before is None else "modified", "content": content}
            )
    return out


def release_controls_unchanged(files: list[dict[str, Any]]) -> bool:
    return all(f["path"].startswith(TESTS) for f in files) and not any(f["path"] == PIPELINE for f in files)


def merge(repo: Path, approved: list[str], reviewer: tuple[str, str]) -> dict[str, str]:
    """Commits the approved items on the branch and merges it into main, as the reviewer."""
    chosen = [item for item in items() if item["item_id"] in approved]
    files = {f["path"]: f["content"] for f in changed_files(repo)}
    paths = {p for item in chosen for p in item["files"]}
    data_path = TESTS + maintenance.DATA_FILE
    test_data = _in_repo(repo, data_path) or ""
    for item in chosen:
        if item["kind"] == "test":
            data = item["data"]
            entry = f"export const {data['group']} = {{\n  {data['key']}: '{data['value']}',\n}};"
            test_data = maintenance.merged_test_data(test_data, entry)
        elif data_path in item["files"]:
            test_data = maintenance.merged_test_data(test_data, files[data_path])
    status = _git(repo, "status", "--porcelain")
    if status.strip():
        raise RuntimeError("The module repository has uncommitted changes.")
    _git(repo, "checkout", "-q", "-B", BRANCH, "main")
    for path in sorted(paths - {data_path}):
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[path].rstrip() + "\n", encoding="utf-8", newline="\n")
    (repo / data_path).write_text(test_data.rstrip() + "\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "-A", TESTS)
    titles = "\n".join(f"- {item['item_id']}: {item['title']}" for item in chosen)
    _git(repo, "commit", "-q", "-m", f"Add proven billing tests and fix two flaky tests\n\n{titles}")
    branch_commit = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "checkout", "-q", "main")
    # Main has not moved since the branch was cut, so the merged tree is the branch's tree. Writing the
    # merge commit directly, with both parents, avoids git merge stashing files whose timestamps the
    # mounted folder reports as changed.
    message = f"Merge {PR_ID}: {BRANCH}\n\nApproved by {reviewer[0]}."
    tree = _git(repo, "rev-parse", f"{BRANCH}^{{tree}}").strip()
    merge_commit = _git(repo, "commit-tree", tree, "-p", "main", "-p", BRANCH, "-m", message, author=reviewer)
    merge_commit = merge_commit.strip()
    _git(repo, "update-ref", "refs/heads/main", merge_commit)
    _git(repo, "reset", "-q", "--hard", "main")
    return {"branch": BRANCH, "branch_commit": branch_commit, "merge_commit": merge_commit}
