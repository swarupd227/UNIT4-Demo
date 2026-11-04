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
| `estate/test-data` | The test data catalogue: what the seeded test environment holds |
| `faults` | 34 seeded faults, each tagged to a rule |
| `generation` | The automation batch the quality engineering lead chose |
| `generated` | Every generation attempt: candidate tests, their test data and their checks |
| `lab` | The test lab image: every build of the module plus Playwright, and the run harness |
| `answer-key` | What the right answers are, written before any agent runs |
| `engines` | Shared Python: estate reader, coverage, defect history, dead code, the context analysis, agent gateway, audit trail, ontology |
| `agent-recordings` | Recorded results of the context agents, replayed by the workbench. Each holds the hash of its input and prompt |
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
npm run qe:record
```

Records the context agents (case and defect mapping, the hidden-rule finder, risk cards) with Claude. It calls the model only where a recording is missing or its input or prompt has changed, and saves a result only after it passes the same checks as in the app. Needs `ANTHROPIC_API_KEY` in `.env`. Restart `qe-api` afterwards so the workbench replays the new recordings.

```bash
npm run qe:generate -- 1
npm run qe:prove -- 1
npm run qe:generate -- 2
npm run qe:prove -- 2
```

Generates tests for the batch in `generation/batch.yaml`, then proves them. Attempt 1 reviews each manual case against the documents, merges duplicates and skips cases an existing test already covers, then writes a test for every source. A validator agent that never sees the test works out each expected value from the documents. The lab runs the whole suite 20 times with the candidates added, and runs the candidates on their rules' seeded faults. Attempt 2 regenerates only the tests that failed a check, with the reasons. Candidates and their checks are in `generated/attempt-<n>`, and lab results in `lab/results/proof`.

```bash
docker run --rm --entrypoint cat qe-lab /seed/billing.db > qe/estate/test-data/seed.db
docker compose -f docker-compose.qe.yml exec -w /workspace qe-api python -m qe.tools.export_test_data /workspace/qe/estate/test-data/seed.db
```

Rewrites the test data catalogue after a change to the seed data.

```bash
npm run qe:maintain -- flaky
npm run qe:maintain-lab -- flaky
npm run qe:maintain-lab -- release
npm run qe:maintain -- repair
npm run qe:maintain-lab -- repair
```

Reliability and maintenance. The diagnoser finds and fixes each flaky test in `lab/results/baseline-20.jsonl`, and the lab proves the fixes over 20 runs. Then the suite runs on the next release (`faults/releases.yaml`), the repairer fixes the selectors it broke, and the lab proves the repair. All results go to `lab/results/maintenance`.

```bash
npm run qe:reset
```

Puts the workbench back to the start for a rehearsal. It rebuilds the module repository, which reopens the pull request, and clears every review, merge and audit event. Recordings and lab results are kept.

## On stage

```bash
npm run qe:demo
```

Starts the workbench as presented: a production build on http://localhost:5194, the API, and the lab runner for the one live check in the Proof scene. In the audience window, Ctrl+Alt+P opens the presenter console. It shows each scene's notes and time budget and moves the audience window between scenes. It can also play a scene's recorded fallback and reset the workbench to the start. The arrow keys move between scenes in either window.

```bash
npm run qe:rehearse
npm run qe:record-fallbacks
```

`qe:rehearse` runs the whole journey in script order against the production build, starting from a reset. It covers the live fault run and the engineer's real merge, and checks that every scene is ready within two seconds. `qe:record-fallbacks` runs the same journey and keeps each scene's video in `apps/qe-web/public/fallback`, for the console's Play recording. Restart `qe-web-demo` afterwards so the build includes them.

```bash
node demo-video/qe/record.mjs
cd demo-video/qe && node assemble.mjs
```

Records the 3 to 4 minute video against `npm run qe:demo`, in the same format as the Migration Studio video. Each scene has one caption, and Artizent screens open and close it. The kit lives in the git-ignored `demo-video/qe` folder, and the finished video goes to `deliverables/`.

```bash
npm run qe:verify
```

Checks rules, cases, documents, faults, dead code, defects, history and the lab results against the answer key.
