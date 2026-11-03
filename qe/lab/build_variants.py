"""Builds the billing module once as it is and once per seeded fault.

Each fault is applied to its own copy of the source, so a build is exactly one fault away from
the baseline. Output: /builds/baseline and /builds/<fault id>, each a published app.
"""

import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

SOURCE = Path("/work/src")
VARIANTS = Path("/work/variants")
BUILDS = Path("/builds")
PROJECT = "Billing.Web/Billing.Web.csproj"


def apply(fault: dict, root: Path) -> None:
    path = root / fault["file"]
    text = path.read_text(encoding="utf-8")
    count = text.count(fault["find"])
    if count != 1:
        sys.exit(f"{fault['id']}: expected the change to match once in {fault['file']}, found {count}")
    path.write_text(text.replace(fault["find"], fault["replace"]), encoding="utf-8")


def publish(name: str, root: Path) -> str:
    result = subprocess.run(
        [
            "dotnet",
            "publish",
            str(root / PROJECT),
            "-c",
            "Release",
            "-o",
            str(BUILDS / name),
            "--nologo",
            "-v",
            "q",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"{name}: build failed\n{result.stdout[-3000:]}"
    return f"{name}: built"


def main() -> None:
    faults = yaml.safe_load(Path("/work/faults/faults.yaml").read_text(encoding="utf-8"))["faults"]
    jobs = [("baseline", SOURCE)]
    for fault in faults:
        root = VARIANTS / fault["id"]
        shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns("bin", "obj"))
        apply(fault, root)
        jobs.append((fault["id"], root))

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda job: publish(*job), jobs))
    for line in results:
        print(line)
    if any("failed" in line for line in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
