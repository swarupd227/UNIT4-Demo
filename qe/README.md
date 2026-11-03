# Test Assurance Studio: project billing

Use case 2. The plan is in [docs/USE_CASE_2_PLAN.md](../docs/USE_CASE_2_PLAN.md). The workbench is in `apps/qe-api` and `apps/qe-web`; this folder holds what it works on.

| Folder | What it is |
|---|---|
| `estate/src` | The legacy billing module: .NET 8 Razor Pages on SQLite |
| `estate/tests/e2e` | Its 12 existing Playwright tests, page objects and fixtures |
| `estate/docs` | 28 help pages and the business rule register (20 rules, 12 critical) |
| `estate/manual-cases` | 40 manual test cases, Azure DevOps CSV export |
| `estate/defects` | 120 defects, Azure DevOps bug export, each linked to its fix commit |
| `history` | The module's three-year Git history: `timeline.yaml` and the tool that builds `history/repo` from it |
| `faults` | 34 seeded faults, each tagged to a rule |
| `lab` | The test lab image: every build of the module plus Playwright, and the run harness |
| `answer-key` | What the right answers are, written before any agent runs |
| `engines` | Shared Python: estate reader, agent gateway, audit trail, ontology |
| `tools/verify.py` | Checks the estate against the answer key |

## Commands

```bash
npm run qe:dev
```

Starts the workbench on http://localhost:5193 (API on 8030) and the billing module on http://localhost:5280.

```bash
npm run qe:lab -- --builds baseline --runs 20 --parallel 3 --out /results/baseline-20.jsonl
```

Repeat runs of the existing tests, each on a fresh copy of the seeded database.

```bash
npm run qe:lab -- --builds all --workers 1 --confirm 5 --parallel 3 --out /results/fault-check.jsonl
```

The fault check. A test catches a fault only when it fails on five runs of that faulted build, each on a fresh database.

```bash
docker run --rm -v "$PWD:/repo" -w /repo python:3.13 sh -c "pip install -q pyyaml && python qe/history/build_history.py"
```

Rebuilds the history repository and the defect export. Run it after any change to the module, its tests or its help pages, because the history ends at today's files.

```bash
npm run qe:verify
```

Checks rules, cases, documents, faults, dead code, defects, history and the lab results against the answer key.
