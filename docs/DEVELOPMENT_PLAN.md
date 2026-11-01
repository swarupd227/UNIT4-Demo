# Unit4 CR to ERPx Migration Studio: Development Plan

Source: *Unit4 CR to ERPx Migration Acceleration, Demo Specification* (Artizent, 31 October 2026).
Scope: the migration workbench and its engines, built and run locally first, then deployed to Azure.

---

## 1. What we are building

One web app, **Migration Studio**, in which a consultant takes the fictional customer Ardleigh Consulting Group from J2X.AI output to a customer sign-off pack in about 22 minutes on stage.

Four rules shape the whole build:

| Rule | What it means in the build |
|---|---|
| Nothing moves without a person | Agents only ever write *proposals*. Decisions and approvals are separate records, written only by a named role |
| The language model never judges numbers or controls | Reconciliation, parity and rule tests are plain code. The UI labels every output as "AI analysis" or "Verified by code" |
| It must not fail on stage | Replay mode is the default. Agent results are cached, so the full demo runs with no LLM key and no network |
| Results are measured, not asserted | The scorecard computes its numbers from the database against the answer key. Nothing on it is hard-coded |

---

## 2. Working assumptions

- **Build team:** Claude Code builds in this folder, with you reviewing at each phase gate. The spec's 7-person, 648-hour, 3-week plan is used as the task list (numbers `#1` to `#21` below), not as a staffing plan.
- **Astra assets:** the Astra RE Harness and Data Factory runtime are not in this folder. Code reading goes behind an interface, with a direct LLM implementation first. The harness can be swapped in later.
- **Target:** a simulated ERPx target from day one, behind the same interface a real test tenant would use. The UI states this openly, as the spec requires.
- **Name:** "Migration Studio" in the product, replacing "migration workbench".

---

## 3. Spec issues to resolve before building

These are contradictions or gaps that a Unit4 expert in the audience would notice, or that would break the scorecard. Each has a build decision, so **none of them blocks the start**. The functional specialist (FS) should confirm items 1 to 8.

| # | Issue in the spec | Why it matters | Build decision |
|---|---|---|---|
| 1 | **£1,240.50 "rounding" (M7) is not arithmetically possible as line rounding.** 3,100 items at up to half a penny each is at most £15.50 | CR experts will spot this on stage | Plant it as an **exchange-rate precision** difference: revaluation rate held at fewer decimals on the foreign-currency balance. Tune the generator so it produces exactly £1,240.50 |
| 2 | **Report parity contradicts the partner-list fix (M4, R7).** If the rebuild uses current partners but CR uses a stale list, totals cannot match | Scene 4 and R7 both claim a match | Two-step parity. Step 1: faithful rebuild, stale list, totals match exactly (logic proven). Step 2: fixed list, difference equals exactly the WIP of the omitted partners, and is shown as an explained reconciling item |
| 3 | **R6 as written passes M6.** "Each CR value maps to exactly one ERPx value" is true when two accounts map to one target | The check would not catch the planted issue | Define R6 as four sub-rules: unmapped, one-to-many, many-to-one with conflicting attributes (VAT, catches M6), and duplicates after normalising (catches M9) |
| 4 | **Retire rule misses RP-112 and WF-006.** Both ran in the last 12 months, so "not used in 12 months" never proposes retiring them, yet M3 and M5 depend on that | The "system refused to retire" moment has no trigger | Add a **low-use band** (at most 2 runs in 12 months) that makes an item a retire candidate. The override flags then stop RP-112. A separate "dormant entity only" signal covers WF-006 |
| 5 | **"Ask customer" is not one of the five outcomes**, but the mock-up shows it as a decision. M10 also needs "no automatic decision" | "Every item gets one of five" is not literally true | Split the model into `outcome` (the five, nullable) and `state`. A held item has no outcome and shows "Held: needs customer" |
| 6 | **Reports do not fit the five outcomes.** "Merge" is not an outcome, and read-only rebuilds fall under "Keep and re-point" by the flowchart, yet the mock-up says "Rebuild" | Register and flowchart disagree on screen | Reports use the five outcomes plus an `action` detail (merge, rebuild layout). RP-077 becomes "Keep and re-point · rebuild". FS to confirm the wording |
| 7 | **CC-014 fits M10's own rule.** It is undocumented and ownerless, which M10 says means "interview, no automatic decision" | The hero item contradicts a planted rule | M10 is a *different* item whose purpose cannot be established from its code. CC-014 gets a decision because its code is readable and it runs daily; the missing owner shows as a risk |
| 8 | **"No employee data" conflicts with M4 and "Utilisation by grade".** Both need partner and grade reference data | The opening statement could be challenged | Use a minimal invented **resource reference** (name, partner flag, grade) with no HR attributes. Say "no real data, no payroll or HR data" |
| 9 | **M2, M9 and M10 have no scene or screen**, but the scorecard needs all ten found | The demo could "pass" without the audience seeing them | M2: dependency panel on the Code screen. M9: R6 drill-down. M10: a "Held" filter chip on Decisions |
| 10 | **Sign-off needs "no open questions", but scene 7 shows open questions** and R8 needs a threshold nobody has chosen | The sign-off claim fails on its own measure | Questions block the sign-off gate. In scene 6 the presenter switches to the customer, picks the threshold, tests regenerate and R8 turns green. Sign-off scope is "trial migration accepted, with listed exceptions", never cutover readiness |
| 11 | **Cached results distort "elapsed time".** Replay finishes in seconds | The scorecard would overstate speed | Each cached result stores its original run duration. The scorecard shows that, labelled "recorded run" |
| 12 | **Product-gap counts need other customers**, but the demo has one | Mapping memory would be empty | Seed a few synthetic precedents from other fictional customers and label them synthetic |
| 13 | **No dormant entity exists for M5.** The spec lists three legal entities, all active, but M5 needs a dormant one, and the mock-up labels WF-006 "NL" | WF-006 has no entity to be dormant in | Add a dormant fourth company, Ardleigh Advisory Holding B.V. (NL02, dormant since June 2023). It sits outside the three trading entities |
| 15 | **Agent inputs do not exist until Phase 3.** The Decisions screen needs proposals now | Proposals could otherwise be copied from the answer key, which would fake the score | The rules run on labelled stand-in signals in the agents' output shape, with deliberate misses. Phase 3 replaces the signals, not the rules |
| 16 | **The live report counts differ from the spec by design.** The spec plans 61 retire and 18 rebuild, but RP-058 and RP-112 are held for the customer | Forcing the planned numbers would hide the held items | The screen shows 60 retire, 38 into 9, 31 standard, 17 rebuild and 2 held, which adds to 148. The planned figures apply once the customer answers |
| 17 | **A signature beside "1 of 233 agreed" is not credible.** Nobody clears 233 items live | Experts would question the sign-off | Routine decisions start agreed: consultant-only, confidence 85 or above, no flags, no configuration. They are labelled seeded demo history in the audit trail, detail panel and pack |
| 14 | **The rebuild reports have no home for RP-112.** The 148 must still add up with the audit pack held for the customer | The report totals could drift | RP-112 is counted within the 18 rebuilds, with state "held" until the customer confirms it |

Minor: "built up over 15 years" against a 2009 start is 17 years. The mock-up's tabs omit Customer card and Scorecard, so the plan treats those as the start and end of the journey rail.

---

## 4. Architecture

```
React SPA  ──REST + SSE──▶  FastAPI  ──▶  PostgreSQL (decisions, memory, audit, CR + ERPx simulated data)
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       Agent layer       Decision engine   Validation engine
       (AI: analyse,     (rules + flags,   (deterministic:
        generate)         code only)        R1 to R8, parity)
              │                                 │
       LLM gateway                        ErpxTarget interface
       replay | live                      simulated | real tenant
```

| Layer | Choice | Why |
|---|---|---|
| Web | React 19, TypeScript, Vite | The spec's React SPA, with fast iteration |
| UI primitives | Tailwind 4, Radix, own component layer | Accessible behaviour with fully custom visuals, so it does not look like a template |
| Data UI | TanStack Query, Table and Virtual | Register and drill-downs stay smooth at thousands of rows |
| Motion, charts, code | Motion, visx, Shiki | Choreographed transitions, bespoke charts, read-only code with line anchors |
| API | Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic | One language with the engines. Pinned in Docker, because the machine's 3.14 is too new for some libraries |
| Decision and validation | Python. Checks are versioned YAML + SQL definitions | The spec's "versioned definitions". Money is stored as integer minor units, never floats |
| Store | PostgreSQL 16 + pgvector | Relational data, dependency edges and mapping-memory similarity in one store. Also available on Azure |
| LLM | Provider-neutral gateway; Claude as default | The spec's model-agnostic requirement. Structured output validated with Pydantic |
| Sign-off pack | HTML to PDF (WeasyPrint), plus a ZIP with a hash manifest | One styled document with verifiable evidence |
| Progress | Server-sent events with heartbeats | Live runs in the UI; simpler than WebSockets |

**Local to Azure mapping.** Everything is containerised and configured by environment variables from the first commit, so the move is a deployment rather than a rewrite.

| Concern | Local | Azure |
|---|---|---|
| Web | Vite dev on port 5183, then nginx container | Azure Static Web Apps or Container Apps |
| API | Docker Compose | Azure Container Apps |
| Database | `pgvector/pgvector:pg16` | PostgreSQL Flexible Server with the `vector` extension |
| Files | Local folder behind a storage interface | Blob Storage |
| Secrets | `.env` (git-ignored) | Key Vault with managed identity |
| LLM | Replay cache, optional direct API key | Azure-hosted model. Confirm Claude availability, region and data residency |
| Sign-in | None; persona switcher only | Microsoft Entra ID in front of the app |
| Telemetry | Console logs | Application Insights |

### Repository layout

```
apps/web/               React app: design system, shell, nine screens
apps/api/               FastAPI: routes, services, migrations
engines/decision/       Rules, override flags, mapping memory
engines/validation/     Check runner, R1 to R8 definitions, parity
engines/agents/         Analysers, generators, gateway, replay cache
data/generator/         Seeded synthetic estate generator (reproducible)
data/fixtures/          Hand-written hero items: CC-014, RP-077, RP-112
data/answer_key/        Expected decisions and M1 to M10
infra/                  Bicep templates (Azure phase)
docs/                   Plan, demo script, decision log
docker-compose.yml
```

### Core data model

- **Estate:** `customer`, `migration_case`, `estate_item` (CC, RP, WF, CF), `usage_event`, `dependency`, `j2x_explanation`
- **Decisions:** `proposal` (agent, evidence, confidence), `decision` (outcome, state), `approval` (role, person, timestamp), `customer_question`
- **Artefacts:** `artefact` (explanation, rule card, extension spec, tests, config), `mapping_memory`
- **Validation:** `check_definition`, `check_run` (with input and result hash), `check_result`, `exception`
- **Evidence:** `signoff_pack`, `timing_event`, and an append-only, hash-chained `audit_event`
- **Data:** separate schemas `cr_source` and `erpx_sim`, so loading the target can only go through `ErpxTarget`

The answer key lives in its own schema, read only by the scorer. This stops it leaking into agent inputs or the UI.

---

## 5. UX plan

The standard: it should feel like a product people would choose to work in, and read clearly from the back of a boardroom. The audience is expert and sceptical, so **trust is the UX goal**: every claim must be one click from its proof.

### Design principles

1. **Proof one click away.** A single `EvidenceChip` pattern opens the source everywhere: usage log, code line, policy paragraph or data row. No claim appears without one.
2. **Proposal and decision look different.** Agent proposals are visibly provisional. A confirmed decision shows who approved it and when. The system's "I won't decide this" state is designed with as much care as its answers.
3. **Two marks of provenance.** "AI analysis" and "Verified by code" are distinct, consistent badges on every result. This makes the spec's core architecture visible without explaining it.
4. **One calm spine.** The customer bar holds position, always showing the customer, and live counts of decided items, open questions and exceptions. A journey rail shows the nine stages.
5. **Stage-legible first.** Designed at 1920×1080 for a projector: 16px minimum body text, 14px minimum in dense tables, high contrast, and one focal point per screen.
6. **Motion carries meaning.** Numbers count, checks tick in sequence and 148 visibly collapses to its groups. Durations are 150 to 250ms for interface moves, with `prefers-reduced-motion` respected.
7. **Instant by default.** Cached scenes load in under a second, with skeletons shaped like the real content. Long runs show named steps rather than a spinner.
8. **Keyboard-first for consultants.** `J`/`K` to move, `A` accept, `E` edit, `Q` ask customer, `Ctrl+K` command palette, `/` search.
9. **Accessibility is baseline.** WCAG 2.2 AA, full keyboard paths and status conveyed by icon and text as well as colour.
10. **Their language.** All CR and ERPx terms live in one glossary file, so the FS can correct terminology without touching screens. Copy is British English, numbers use tabular figures, and money is formatted `en-GB`.

Visual direction: a restrained, warm-neutral base with a single strong accent, one type family with tabular numerals, and semantic status colours used sparingly so that a red conflict really stands out. Light theme for projectors, with dark as a token swap. It carries Artizent branding, not Unit4's logo or identity.

### Signature moment per screen

| Screen | Layout | The moment that sells it |
|---|---|---|
| **Customer card** | Hero summary with estate tiles | The "all data is synthetic" statement is designed in, not a footnote |
| **Estate** | Load sequence, then estate map by type | Sources arrive one by one, with a clear J2X layer: "already explained by J2X", then "where we start" |
| **Decisions** | Register with detail panel, as in the mock-up | Filter to Retire, and RP-112 stands out as refused, with its "year-end" trigger highlighted in the evidence |
| **Code** | Three linked panes: source, plain English, rule card | Hover a rule and its source lines light up. The 10% against 15% conflict appears side by side, with an M2 dependency panel beneath |
| **Reports** | Reduction view, then parity table | 148 collapses into retire, merge, standard and rebuild. Then a two-step parity run reveals the stale partner list |
| **Workflows** | Variants ranked by usage, before and after | 9 becomes 3, with the dormant NL variant fading out and its evidence attached |
| **Reconcile** | Eight check cards, then row drill-down | Checks run in sequence. One click traces £1,240.50 to its rows. A re-run gives an identical hash, proving determinism. The customer picks a threshold and R8 turns green |
| **Sign-off** | Pack preview beside a gate checklist | The checklist blocks signing until it is clear, then a PDF with a verifiable manifest is generated |
| **Scorecard** | Measures grouped by stage | 10 of 10 planted issues found, false items counted, and "from J2X" and "pilot measure" shown honestly in place of savings figures |

### Presenter tooling (hidden from the audience)

- **Persona switcher** in the customer bar: consultant, customer finance lead, Unit4 technical lead, Unit4 product team. This shows who approves what with one presenter.
- **Presenter mode:** private scene timer, `←`/`→` between scenes, and a per-scene note.
- **One-key reset** to the start state in seconds, plus resuming at any scene.
- **Scene safety net:** a switch to the recorded fallback for a scene.
- **Rehearsal readout:** actual time per scene against the 22-minute budget.

---

## 6. Delivery phases

Each phase ends in something runnable, with an exit gate. Build order is deliberate: data first because everything depends on it, and one screen polished to full standard before the others copy it.

### Phase 0: Foundations (done)
Git repo, monorepo layout, Docker Compose (Postgres, API, web), migrations, health endpoints, lint, types and test runners, environment-based config, storage and LLM interfaces.
**Exit:** one command starts the stack, and a page reads from the database through the API.

### Phase 1: Synthetic estate and answer key (`#1`–`#7`) (built; awaiting FS review)
Hand-write CC-014 and the other two detailed code items, the policy document, and RP-077 and RP-112. Generate the rest with a seeded generator: 64 code items, 148 reports with 12 months of usage, 9 workflows, 14 integrations, about 2,300 accounts, 3,100 receivables, 1,450 payables, 860 projects, and a simulated J2X report. Plant M1 to M10 using the fixes in section 3. Run the migration into `erpx_sim` through the real mapping, so the differences arise naturally. Build the answer key.
**Exit:** the same seed gives byte-identical data; a validation script confirms all spec counts and every planted issue; FS has reviewed the estate.

### Phase 2: Design system and Decisions vertical slice (part of `#16`, part of `#10`) (built; awaiting UX gate)
Tokens, typography, app shell, customer bar, journey rail, data grid, evidence drawer, provenance badges, states, glossary. Then the **full Decisions screen** end to end: real data, accept, edit, ask customer, role rules, audit trail.
**Exit (UX gate):** you review Decisions at 1080p and on a projector if possible. Its quality becomes the bar for the rest. **This is the most important checkpoint in the plan.**

### Phase 3: Engines (`#9`–`#15`) (done, with authored agent results)
- Decision engine: tree, low-use band, override flags, mapping memory, role rules
- Validation engine: R1 to R8, drill-down data, exception creation, run hashes
- Agent layer: code explainer, rule extractor, report clustering, workflow analysis, spec and test generators. Run once and commit results to the replay cache, with schema validation
- Scoring harness against the answer key

**Exit:** the harness finds 10 of 10 issues with at most 3 false items; validation runs twice with identical hashes; everything runs with no network.

Status: all three met, on a Docker network with no internet route. Report clustering, workflow grouping and stale-list detection are plain code over the estate. Code reading has no key yet, so CC-014, CC-037 and CC-041 artefacts are hand-authored in the agents' schema and marked `hand_authored`, with no recorded run time. A live provider implements the same gateway `run` once a key exists. pgvector is enabled but unused: precedents match on exact pattern until embeddings are available.

If no LLM key is available yet, the replay cache is hand-authored in the same schema, and the live run is added once a key exists.

### Phase 4: Remaining screens (`#16`–`#18`) (built)
Customer card, Estate, Code, Reports, Workflows, Reconcile, Sign-off and Scorecard, all to the Phase 2 standard, along with the PDF pack and ZIP manifest.
**Exit:** the full journey runs start to finish on real local data, with the sign-off gate working and a scorecard computed from the database.

### Phase 5: Stage readiness (`#19`–`#21`) (built; human rehearsals and specialist review outstanding)
Presenter mode, reset, fallback switch and recordings, performance pass, accessibility audit, FS terminology review, timed rehearsals.
**Exit:** three clean timed runs of 22 minutes or less; every scene loads in under 2 seconds; zero critical accessibility issues.

Status: three consecutive clean scripted passes on the production build, with every scene under 2 seconds and no critical or serious axe findings. A presenter's 22-minute timing still needs a person. An earlier run saw loads up to 3.8 seconds; the cause was not isolated, so present with `npm run demo` and other Docker projects closed.

### Phase 6: Azure deployment
Bicep for Container Apps, Postgres, Blob Storage, Key Vault, Container Registry and Application Insights. Add Entra sign-in and a CI pipeline, then install the Azure CLI, which this machine does not have yet.
**Exit:** a full rehearsal passes on the Azure URL, with replay mode behaving identically to local.

---

## 7. Quality gates

| Layer | What runs |
|---|---|
| Engines | Unit tests per rule and check; a determinism test comparing hashes between runs |
| Demo correctness | Scorer against the answer key on every change; fails if any planted issue is missed |
| API | Contract tests, including that agents cannot create approvals |
| UI | Playwright run of the full 22-minute journey, plus visual snapshots of each screen at 1920×1080 |
| Accessibility | axe in Playwright, with manual keyboard and contrast checks |
| Performance | Scene load under 2 seconds; register scrolling smooth with all 233 decision items (247 estate items less the 14 integrations) |

---

## 8. Needed from people

| Item | From | Needed by | If it is not available |
|---|---|---|---|
| Unit4 FS review of estate, terms and items 1 to 8 in section 3 | Functional specialist | Phases 1 and 5 | The plain terms in the spec stay, at a credibility risk |
| LLM API key | You | Phase 3 | Hand-authored cache; the demo still runs, but it cannot make a live agent call |
| Astra RE Harness access | Artizent | Phase 3 | Direct LLM code reading behind the same interface. The "built on Astra" claim should then be softened on stage |
| Azure subscription, resource group and Entra access | Artizent | Phase 6 | Stays local |
| ERPx test tenant | Unit4 | Optional | Simulated target, stated openly |
| Real J2X format | Unit4 | Optional | Simulated output, swappable through its parser |

## 9. Main risks

| Risk | Mitigation |
|---|---|
| Polished UI on thin CR knowledge loses expert trust | FS review gates, glossary file and the realistic mess in the estate |
| UX polish consumes the time for the core story | Scenes 2, 3 and 6 are finished first; scenes 4 and 5 can ship simpler if needed |
| Generated data does not hit exact planted figures | Hero rows are hand-fixed, and the validation script runs on every generation |
| The demo looks staged because everything is cached | One optional live step (explaining a single code item), and honest labelling of recorded runs |
| Windows-only behaviour slips in | All backend code runs in Linux containers from the first commit |
