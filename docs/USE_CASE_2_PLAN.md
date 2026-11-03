# Use case 2: Test Assurance Studio — Development Plan

Source: *Unit4 Automated Testing and Context for Agentic Engineering, Demo Specification* (Artizent, 31 October 2026), RFP use case 2, optional scope.

Working name: **Test Assurance Studio**. The name is provisional, so change it before the screens are built.

## 1. What the demo must do

It takes one legacy functional area, project billing, from "not ready for the MOSAIC gate" toward it, in about 20 minutes. Agents:
1. map coverage against business rules;
2. mine defects and fixes into reviewed context;
3. turn manual Azure DevOps cases into Playwright tests in the existing conventions;
4. prove each new test independently: a validator agent, seeded faults and 20 repeat runs;
5. diagnose flaky tests.

An engineer accepts every test through a pull request, and release controls do not change. The remaining gaps are ranked by risk, and the RFP's measures are scored.

The hardest requirement: **real tests must run against real code.** Unlike use case 1, the module, its tests and its faults cannot be data alone. They must execute, so most of the risk sits in building a believable legacy module.

## 2. Reuse from Migration Studio

| Reused as is, or adapted | Why |
|---|---|
| Stack: React 19, Vite, Tailwind, FastAPI, Postgres, Docker Compose | Proven, and already in the repository |
| Agent gateway: replay and live, structured output, citation checks, input hashes | Every agent result is checked the same way |
| Migration Ontology | BR-07 is the same write-down rule as CC-014. Grounding risk cards and hidden rules in the same billing concepts tells one Artizent story across both use cases |
| Hash-chained audit trail, named roles, answer key and scorer | Engineer accountability and a measured scorecard |
| Product-wording rules, Sandbox label, provenance badges (Prepared analysis, AI analysis, Verified by code) | Lessons from use case 1 |
| Presenter console, fallback recordings, rehearsal test, demo video kit | Stage readiness and the 3 to 4 minute video format |

**Decision: same repository, separate application.** It lives at `apps/qe-web`, `apps/qe-api` and `qe/` (module, test estate, engines), with its own Compose project and ports. The Migration Studio demo cannot break, and the shared parts are copied in, not edited in place. Ports: web 5193, API 8030 (8010 is taken on this machine), module 5280, Postgres 5554.

## 3. Architecture

| Part | Built as | Real or stand-in |
|---|---|---|
| Legacy billing module | .NET 8, ASP.NET Core Razor Pages, EF Core on SQLite, so every test run gets its own fresh copy of the seeded database in milliseconds; about 3,800 lines with long methods, a shared `BillingHelper` and `RoundingHelper`, and undocumented rules | Real code, synthetic content |
| Module history | A real Git repository: three years of commits, 120 defects, fix commits linked by ID, some fixes without tests | Real history, synthetic content |
| Manual test cases | 40 cases in Azure DevOps CSV export format, with steps and expected results | Real format, synthetic content |
| User documentation | About 25 pages of help text in Markdown | Synthetic |
| Existing automated tests | 12 Playwright tests in TypeScript, with page objects, fixtures and naming conventions; two flaky | Real tests |
| Fault set | About 30 seeded faults as source patches, each tagged to a rule, with each faulted build pre-built as an image | Real faults, compiled and run |
| Test runner | The lab image (`qe/lab`): every build of the module plus Playwright. Each run starts a build on a fresh copy of the seeded database. The fault check runs tests one at a time and repeats a failure on four more fresh databases, so a flaky failure never counts as a catch | Real runs |
| Agents | Coverage mapper, defect clusterer, hidden-rule finder, test generator, independent validator, flaky-test diagnoser, selector repairer | Real Claude calls, recorded for replay |
| Context Engine | A simple store for reviewed entries, exported as structured JSON | Stand-in, labelled |
| Full Circuit pipeline | An `azure-pipelines.yml` in the module repository, plus a local runner that executes its stages | Stand-in, labelled |
| Pull request | A real Git branch and commit, reviewed in the app with all evidence attached | Real Git, stand-in review screen |
| Workbench | React app with 8 screens plus the pull request | Real |

**Who does what, made explicit as in the use case 1 video:**
- **Plain code:** coverage arithmetic, defect clustering by touched code, dead-code reachability, fault runs, 20-run statistics and every score.
- **Agents:** read code and docs, write the hidden rule, generate tests, work out expected results for the validator, explain flaky traces and propose fixes.
- **People:** approve context entries, resolve conflicts, accept or reject each test.

## 4. Specification issues to decide

| # | Issue | Proposed handling |
|---|---|---|
| 1 | "Critical rules covered: 61%" is impossible with 12 critical rules: 7 of 12 is 58% and 8 of 12 is 67% | Show **7 of 12 (58%)**. After the demo's tests, BR-04 and BR-07 move it to **9 of 12 (75%)**. That's still below the 80% gate, so "toward the gate" stays true, and scene 7's gap list shows what remains |
| 2 | Stryker.NET mutates code against **unit** tests, but these are **end-to-end** Playwright tests | Use the spec's own alternative, a **scripted, seeded fault set** (patched and pre-built), and call it a "fault check", not mutation testing. Score per rule = seeded faults caught ÷ faults in that rule |
| 3 | "Passes the mutation check" has no threshold, yet the mock-up shows 92%, 88% and 41% | A rule counts as covered when its tests catch at least 80% of its seeded faults. BR-11 at 41% is then correctly a weak test |
| 4 | The validator must never see generated code | Enforced structurally: its gateway payload contains only the docs, the manual case and the rule. A test proves that no test source reaches it |
| 5 | Live generation varies run to run, but scene 4 needs one weak test (T3) to be rejected | Record real model runs once and replay them, with the T3 weak test kept as a recorded real output. Scene 4's one live run is the validator plus one pre-built fault run |
| 6 | Full Circuit's real conventions are unknown | The 12 existing tests define conventions such as names, fixtures and page objects, and the generator must follow them. On stage, say that these are our conventions, standing in for Full Circuit's |
| 7 | "Manual regression effort" needs minutes for manual runs | Record per-case manual minutes in the answer key as an assumption, labelled. Automated time is measured |
| 8 | Unit4's legacy stack is unknown | Keep the method stack-neutral, and put .NET in a discovery note |
| 9 | Context Engine format, MOSAIC gate rule and Pathfinder scope are unknown | Use our own simple formats, labelled. Don't show Pathfinder |
| 10 | Dead code (T10) "no user can reach" | Plain-code reachability from the module's routes and menus, never an agent's opinion |
| 11 | Escaped defects can't be measured | Shown as a pilot measure, as in the spec |
| 12 | The spec says to state "synthetic" at the start | Follow the use case 1 rule: a Sandbox label in the app, and nothing in the video captions |

## 5. Phases

Each phase ends with a gate: a working build and passing checks, then your review.

| Phase | Builds | Exit gate |
|---|---|---|
| **0. Foundations** | App skeletons, Compose project, schemas, the gateway, audit trail and ontology copied in, product shell and roles: QE lead, engineer, Full Circuit owner | Both apps start beside Migration Studio without disturbing it |
| **1. The legacy module** | The .NET billing module with 20 rules (12 critical) and real legacy traits; seed data and reset; 25 pages of docs; 40 Azure DevOps cases with planted T4, T5 and T8; the Git history of 120 defects with T1 and T9; the 12 Playwright tests with planted T6 and T7; dead path T10; the fault set; the answer key; a verify script | Module runs. The 12 tests run, and two are flaky at measurable rates. Every fault is built and caught or missed exactly as the answer key says. Verify passes |
| **2. Context engines** | Coverage mapping, defect clustering, hidden-rule finder (T2 with code citations, grounded in the ontology), dead-code finder, risk cards and context entries with engineer review and export | Coverage map matches the answer key. BR-04 risk card: 7 defects in `RoundingHelper`, 2 fixes without tests. BR-07 found in code only |
| **3. Generation and proof** | Convention extraction; generator for 5 manual and 4 defect-driven tests; independent validator; fault runner; 20-run runner; T3 reject and regenerate; T4 to a person; T5 asks for an expected result; T8 merged | Every accepted test passes all four checks. T3 is rejected, then accepted after regeneration. No test source reaches the validator |
| **4. Reliability and maintenance** | Flaky triage from 20-run histories and traces (T6 fixed wait, T7 shared data), with fixes applied and re-run; maintenance measure: change a screen label, repair the selector, engineer approves, time measured | Both flaky tests pass 20 of 20 after their fixes. The maintenance time is measured, not assumed |
| **5. Screens and evidence** | Area card, coverage map, risk card, generated tests, proof chain, flaky triage, pull request with full evidence, gap list and pack, scorecard with the RFP measures | Full journey works end to end. Scenes load in under 2 seconds. No critical accessibility issues |
| **6. Stage readiness** | Presenter console, fallback recordings, rehearsal test, demo video, product-wording review | A clean rehearsal run, and a 3 to 4 minute video in the Artizent format |

Phase 3 as built:
- **Batch:** 9 manual cases, the 4 untested rounding defects from the BR-04 risk card, and the approved hidden rule.
- **Intake:** T4 goes to a person and T5 asks for a result. For T8, 48229 merges into 48208, and the existing BR-12 test already covers both, so no new test is written and both cases can be retired.
- **Generated tests:** one per remaining source, 10 in all.
- **Test data:** a project allows only one open proposal, so each test must own its project. Four October projects were added to the seed: P-1021, P-1051, P-1071 and P-1133. Without them, F04d (tax on the unrounded line) could not show on any seeded data.

Biggest risk: **Phase 1.** The module has to feel like real legacy code and behave deterministically under faults, while staying fast enough for 20 runs per test. Build speed matters too: test runs are pre-computed, but one live fault run must finish in seconds.

## 6. What needs people

| Need | From | Without it |
|---|---|---|
| Review of the answer key and the 40 manual cases | A QE lead | The demo grades itself |
| Unit4's legacy stack, MOSAIC gate rule and Context Engine format | Unit4, through discovery | Our stand-ins, labelled |
| LLM key | Already in `.env` | — |
| Rehearsal and specialist review | You and Artizent | As for use case 1 |

## 7. What we will not claim

- No productivity multiple, and no coverage figure for Unit4's real code.
- Generated tests always need an engineer's approval.
- No refactoring of core code: the demo adds tests and context only.
- Our pipeline, Context Engine and conventions stand in for Full Circuit's. They don't replace them.
