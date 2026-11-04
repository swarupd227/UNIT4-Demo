"""Builds the Project Billing Git history from timeline.yaml.

Reverse construction: start from today's tree, undo the commits newest-first to get the initial
import, then create a fresh repository and replay every commit forward with fixed names and dates.
The replayed HEAD must equal today's tree byte for byte.

Outputs:
  qe/history/repo                         the repository (deleted and recreated on every run)
  qe/estate/defects/billing-defects.csv   Azure DevOps bug export
  qe/answer-key/defects.yaml              answer key

Run from the repository root:
  docker run --rm -v <Unit4>:/repo -w /repo python:3.13 \
    sh -c "pip install -q pyyaml && python qe/history/build_history.py"
"""

import csv
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
QE = HERE.parent
ESTATE = QE / "estate"
REPO = HERE / "repo"
WORK = REPO
TIMELINE = HERE / "timeline.yaml"
FAULTS = QE / "faults" / "faults.yaml"
CSV_OUT = ESTATE / "defects" / "billing-defects.csv"
KEY_OUT = QE / "answer-key" / "defects.yaml"

# Where today's code lives, and where it goes in the repository.
SOURCES = [
    (ESTATE / "src" / "Billing.Web", "src/Billing.Web", {"bin", "obj", ".vs"}),
    (
        ESTATE / "tests" / "e2e",
        "tests/e2e",
        {"node_modules", "test-results", "results", "playwright-report", "blob-report"},
    ),
    (ESTATE / "docs", "docs", set()),
]
SKIP_FILES = re.compile(r"(\.db|\.db-shm|\.db-wal|\.user|\.suo|\.log)$", re.I)

ROOT_GITIGNORE = b"""bin/
obj/
.vs/
*.user
*.db
*.db-shm
*.db-wal
node_modules/
test-results/
playwright-report/
results/
"""

RULE_ID = re.compile(r"\bBR-\d+")


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def final_tree():
    tree = {".gitignore": ROOT_GITIGNORE}
    pipeline = ESTATE / "azure-pipelines.yml"
    if pipeline.exists():
        tree["azure-pipelines.yml"] = pipeline.read_bytes()
    for src, dest, skip_dirs in SOURCES:
        if not src.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
            for name in sorted(filenames):
                if SKIP_FILES.search(name):
                    continue
                full = Path(dirpath) / name
                rel = full.relative_to(src).as_posix()
                tree[dest + "/" + rel] = full.read_bytes()
    return tree


def load_timeline():
    data = yaml.safe_load(TIMELINE.read_text(encoding="utf-8"))
    authors = data["authors"]
    commits = data["commits"]
    defects = {d["id"]: d for d in data["defects"]}
    if not commits or not commits[0].get("initial"):
        fail("the first commit must be the initial import")
    last = None
    for c in commits:
        when = datetime.fromisoformat(c["date"])
        if last and when <= last:
            fail(f"commit dates must increase: {c['message'].splitlines()[0]}")
        last = when
        if c["author"] not in authors:
            fail(f"unknown author {c['author']}")
        for ch in c.get("changes", []):
            if ch["file"].startswith("docs/"):
                fail("commits must not change docs: " + ch["file"])
            if not ch["after"]:
                fail(f"empty after in {c['message'].splitlines()[0]} {ch['file']}")
        for path in c.get("added", []):
            if path.startswith("docs/"):
                fail("commits must not add docs: " + path)
    return authors, commits, defects


def reverse(tree, commits):
    """Undo commits newest-first. Returns the initial tree and, per commit, the edits to replay."""
    state = {k: v.decode("utf-8") if not k.endswith((".png", ".ico")) else v for k, v in tree.items()}
    replay = [None] * len(commits)
    for idx in range(len(commits) - 1, 0, -1):
        c = commits[idx]
        title = c["message"].splitlines()[0]
        edits = []
        for ch in reversed(c.get("changes", [])):
            path = ch["file"]
            if path not in state:
                fail(f"{title}: {path} does not exist at this point")
            text = state[path]
            after, before = ch["after"], ch["before"]
            count = text.count(after)
            if count != 1:
                fail(f"{title}: 'after' occurs {count} times in {path}:\n{after}")
            pos = text.index(after)
            state[path] = text[:pos] + before + text[pos + len(after) :]
            edits.append((path, pos, before, after))
        added = {}
        for path in c.get("added", []):
            if path not in state:
                fail(f"{title}: added file {path} does not exist at this point")
            added[path] = state.pop(path)
        replay[idx] = (list(reversed(edits)), added)
    return state, replay


def rmtree(path):
    def onerror(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def write_tree(state):
    for path, content in state.items():
        full = WORK / path
        full.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8") if isinstance(content, str) else content
        full.write_bytes(data)


def git(*args, env=None):
    result = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(WORK), *args], env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        fail("git " + " ".join(args) + "\n" + result.stdout + result.stderr)
    return result.stdout.strip()


def commit(c, authors):
    a = authors[c["author"]]
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": a["name"],
            "GIT_AUTHOR_EMAIL": a["email"],
            "GIT_AUTHOR_DATE": c["date"],
            "GIT_COMMITTER_NAME": a["name"],
            "GIT_COMMITTER_EMAIL": a["email"],
            "GIT_COMMITTER_DATE": c["date"],
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": str(WORK.parent),
        }
    )
    git("add", "-A", env=env)
    msg = c["message"].rstrip("\n") + "\n"
    msg_file = WORK.parent / ".commit-msg"
    msg_file.write_text(msg, encoding="utf-8", newline="\n")
    try:
        git("commit", "-q", "--allow-empty", "--no-verify", "-F", str(msg_file), env=env)
    finally:
        msg_file.unlink()
    return git("rev-parse", "HEAD")


def build_repo(initial, replay, commits, authors, final):
    # Build in a local temporary directory (bind mounts are slow), then copy into qe/history/repo.
    global WORK
    WORK = Path(tempfile.mkdtemp(prefix="billing-history-")) / "repo"
    WORK.mkdir(parents=True)
    git("init", "-q", "-b", "main")
    for key, value in [
        ("core.autocrlf", "false"),
        ("core.fileMode", "false"),
        ("commit.gpgsign", "false"),
        ("user.useConfigOnly", "false"),
        ("core.safecrlf", "false"),
    ]:
        git("config", key, value)
    hashes = []
    state = dict(initial)
    write_tree(state)
    hashes.append(commit(commits[0], authors))
    for idx in range(1, len(commits)):
        edits, added = replay[idx]
        for path, pos, before, after in edits:
            text = state[path]
            if text[pos : pos + len(before)] != before:
                fail(f"replay mismatch in {path} for {commits[idx]['message'].splitlines()[0]}")
            state[path] = text[:pos] + after + text[pos + len(before) :]
        state.update(added)
        write_tree({p: state[p] for p in set(p for p, *_ in edits) | set(added)})
        hashes.append(commit(commits[idx], authors))

    # HEAD must be today's tree, byte for byte.
    listed = git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
    if sorted(listed) != sorted(final):
        missing = sorted(set(final) - set(listed))
        extra = sorted(set(listed) - set(final))
        fail(f"HEAD tree differs from today's tree. Missing: {missing[:10]} Extra: {extra[:10]}")
    for path, content in final.items():
        blob = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(WORK), "show", "HEAD:" + path], capture_output=True
        ).stdout
        if blob != content:
            fail("HEAD content differs from today's file: " + path)
    if git("status", "--porcelain"):
        fail("working tree not clean after replay")
    # One pack file instead of loose objects keeps the copy onto the bind mount quick.
    git("repack", "-a", "-d", "-q")
    git("prune")
    for hook in (WORK / ".git" / "hooks").glob("*.sample"):
        hook.unlink()
    rmtree(REPO)
    shutil.copytree(WORK, REPO, symlinks=True)
    rmtree(WORK.parent)
    return hashes


SEVERITY = {1: "1 - Critical", 2: "2 - High", 3: "3 - Medium", 4: "4 - Low"}


def ado_date(value):
    d = datetime.fromisoformat(value)
    hour = d.hour % 12 or 12
    return f"{d.month}/{d.day}/{d.year} {hour}:{d.minute:02d}:00 {'AM' if d.hour < 12 else 'PM'}"


def write_outputs(commits, hashes, defects):
    fix_of = {}
    for c, h in zip(commits, hashes, strict=True):
        if c.get("defect"):
            if c["defect"] in fix_of:
                fail("two fix commits for " + c["defect"])
            fix_of[c["defect"]] = (c, h)
    for did in defects:
        if did not in fix_of:
            fail("no fix commit for " + did)

    faults = {f["id"]: f for f in yaml.safe_load(FAULTS.read_text(encoding="utf-8"))["faults"]}

    rows, key = [], []
    for did in sorted(defects, key=lambda d: int(d.split("-")[1])):
        d = defects[did]
        c, h = fix_of[did]
        created = datetime.fromisoformat(d["created"])
        closed = datetime.fromisoformat(c["date"])
        if closed < created or (closed - created).days > 21:
            fail(f"{did}: fix date {c['date']} does not follow created {d['created']}")
        files = sorted({ch["file"] for ch in c.get("changes", [])} | set(c.get("added", [])))
        specs = [f for f in files if f.startswith("tests/e2e/specs/")]
        tests = d["tests"]
        if tests == "automated":
            if not specs:
                fail(f"{did}: automated test claimed but the fix touches no spec")
            tests_text = "Automated test: " + ", ".join(specs)
        elif tests == "manual":
            tests_text = "Manual test case updated"
        elif tests == "none":
            tests_text = ""
        else:
            fail(f"{did}: tests must be none, manual or automated")
        for fid in d.get("faults", []) or []:
            if fid not in faults:
                fail(f"{did}: unknown fault {fid}")
            if "src/" + faults[fid]["file"] not in files:
                fail(f"{did}: fault {fid} is in a file the fix does not touch")
        row = {
            "ID": did.split("-")[1],
            "Work Item Type": "Bug",
            "Title": d["title"],
            "State": d.get("state", "Closed"),
            "Severity": SEVERITY[d["severity"]],
            "Priority": d["priority"],
            "Created Date": ado_date(d["created"]),
            "Closed Date": ado_date(c["date"]),
            "Area Path": "Finance\\Project Billing",
            "Found In Build": d["build"],
            "Reported By": d["reported_by"],
            "Resolved By": c["author_name"],
            "Repro Steps": d["repro"].strip(),
            "Resolution": d["resolution"].strip(),
            "Linked Commit": h,
            "Tests Added": tests_text,
        }
        for value in list(row.values()):
            if RULE_ID.search(str(value)):
                fail(f"{did}: CSV text contains a business rule id: {value}")
        rows.append(row)
        key.append(
            {
                "id": did,
                "title": d["title"],
                "rule": d.get("rule"),
                "cluster": d["cluster"],
                "severity": d["severity"],
                "created": d["created"][:10],
                "fix_commit": h,
                "files": files,
                "tests_added": tests,
                "spec": specs[0] if specs else None,
                "reintroduced_by_fault": bool(d.get("faults")),
                "faults": d.get("faults") or [],
            }
        )

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "ID",
        "Work Item Type",
        "Title",
        "State",
        "Severity",
        "Priority",
        "Created Date",
        "Closed Date",
        "Area Path",
        "Found In Build",
        "Reported By",
        "Resolved By",
        "Repro Steps",
        "Resolution",
        "Linked Commit",
        "Tests Added",
    ]
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

    KEY_OUT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Answer key for the Project Billing defect history (qe/estate/defects/billing-defects.csv).\n"
        "# Written by qe/history/build_history.py. Do not edit by hand.\n"
    )
    KEY_OUT.write_text(
        header + yaml.safe_dump({"defects": key}, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
        newline="\n",
    )
    return fix_of


def main():
    authors, commits, defects = load_timeline()
    for c in commits:
        c["author_name"] = authors[c["author"]]["name"]
        first = c["message"].splitlines()[0]
        if RULE_ID.search(c["message"]):
            fail("commit message contains a business rule id: " + first)
        if c.get("defect") and not first.startswith(c["defect"] + " "):
            fail("fix commit message must start with the defect id: " + first)
    final = final_tree()
    initial, replay = reverse(final, commits)
    hashes = build_repo(initial, replay, commits, authors, final)
    fix_of = write_outputs(commits, hashes, defects)

    print(f"commits: {len(commits)}")
    print(f"defects: {len(defects)}")
    print(f"first:   {hashes[0]}  {commits[0]['message'].splitlines()[0]}")
    print(f"last:    {hashes[-1]}  {commits[-1]['message'].splitlines()[0]}")
    for did in sorted(defects):
        if defects[did]["cluster"] == "Multi-currency rounding":
            c, h = fix_of[did]
            print(f"rounding {did} {h} {c['date'][:10]} {c['message'].splitlines()[0]}")
    tests = {}
    for d in defects.values():
        tests[d["tests"]] = tests.get(d["tests"], 0) + 1
    print("tests:", tests)
    print("HEAD tree matches today's tree.")


if __name__ == "__main__":
    main()
