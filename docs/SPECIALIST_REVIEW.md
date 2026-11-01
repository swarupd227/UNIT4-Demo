# Review Pack for the Unit4 Functional Specialist

Please review this before the demo. We have no CR or ERPx access, so anything below may be wrong in Unit4's terms. Every term shown on screen is in one file, `apps/web/src/lib/terms.ts`, so corrections need no screen changes.

## 1. Terms to confirm

| Shown on screen | Our use | Please confirm or correct |
|---|---|---|
| Custom code, server process, scripted rule, custom table, custom field | The kinds of CR customisation | |
| Enquiry, spreadsheet add-in report, report layout | The kinds of CR report | |
| Approval workflow, variant | CR workflow maps | |
| Dimension, cost centre, service line | Analysis dimensions | |
| WIP, write-up, write-down, billing line | Project billing terms | |
| Replace with standard, rebuild as extension, keep and re-point, flag a product gap, retire | The five outcomes | |
| Extension Kit, App Studio, supported APIs | ERPx extension options, from public sources | |

## 2. Content we invented

| Item | Where | The question for you |
|---|---|---|
| The 24 ERPx standard reports | `data/generator/estate.py` | Which are real, and what are they called? |
| Standard feature names for custom code | `data/generator/estate.py` | Do these features exist in ERPx? |
| ERPx configuration and API steps in the extension spec and workflow pack | `data/fixtures/agent_cache` | Would a Unit4 consultant write it this way? |
| The C# style of CC-014, CC-037 and CC-041 | `data/fixtures/code` | Does this look like real CR customisation? If not, what does? |
| Table names, such as `billing_line` and `zz_` custom tables | The same files | Are these close enough for this audience? |
| The J2X assessment | `data/generator/estate.py` | Any known details of its real format? |
| Six-decimal rates in CR, three on trial load | Reconciliation R2 | Is a rate-precision mismatch believable on a CR to ERPx load? |

## 3. Spec decisions to confirm

Items 1 to 8 and 13 to 17 in section 3 of `DEVELOPMENT_PLAN.md`. The ones most likely to draw a challenge are below.

| Decision | Why it matters |
|---|---|
| The £1,240.50 difference is rate precision, not line rounding | The spec said rounding, which cannot produce this amount on 3,104 items |
| A read-only rebuilt report is "Keep and re-point · rebuild" | The spec's flowchart and mock-up disagree |
| The low-use band is at most two uses in 12 months | The spec's rule never fires for RP-112 or WF-006 |
| The dormant entity NL02 is a fourth company | The spec lists three entities, all trading |
| Partner and grade reference data is synthetic | The spec says no employee data, but two reports need these |
| 81 routine decisions start agreed, labelled as seeded history | Sign-off beside 1 of 233 would not be credible |

## 4. Please walk these screens

Run the demo using `DEMO_SCRIPT.md`, and note anything a Unit4 expert would question. Decisions, Code and Reconcile matter most.
