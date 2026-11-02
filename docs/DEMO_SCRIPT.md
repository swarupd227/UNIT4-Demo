# Demo Script: Migration Studio

About 22 minutes on stage, then 10 minutes of questions. Scenes 2, 3 and 6 are never cut.

## Before you start

1. Run `npm run demo`, not `npm run dev`. It serves the production build, which is what the timings measure. Wait until http://localhost:5184 loads.
2. Close other Docker projects if you can, so nothing competes with the demo. Put the audience window on the projector.
3. Press **Ctrl+Alt+P** in the app to open the presenter console, and keep that window on your laptop. It has no menu entry, so the product shows no presenter controls. It also opens at `/presenter`. The audience cannot see it.
4. In the console, press **Reset**. Check the customer bar reads 82 of 233 agreed, and reconciliation reads Not run.
5. Press Space in the console when you begin. The timer runs only while it is started.

## Controls

| Action | Where |
|---|---|
| Next or previous scene | `→` and `←` in either window, when not typing |
| Start or pause the timer | Space in the console |
| Jump to any scene | The scene list in the console |
| Resume a later scene | Go to it, then **Prepare scene N** |
| Show the recording | **Play recording**, and **Back to live** to return |
| Reset everything | **Reset** in the console |
| Change who you are acting as | Persona menu, top right of the audience window |
| Find any item | `Ctrl+K` |
| Move through decisions | `J` and `K`, then `A` accept, `E` edit, `Q` ask customer, `X` select |

**Prepare scene N** resets first, so it discards anything done so far. Use it to recover, never in the middle of a good run.

## Scenes

The console shows these same notes.

| Scene | Time | Show | Say |
|---|---|---|---|
| 0 Set the scene | 1 | Customer card | Ardleigh wants to reach ERPx with fewer customisations. The app labels this as a sandbox, so say it aloud: everything is synthetic, with no payroll or HR data. The ERPx target is simulated, and the agent results marked Prepared analysis are written by hand, not generated live |
| 1 Load the estate | 2 | Load estate, then the estate map | J2X output arrives first, because this builds on it. J2X explains what exists. We start from there. Time by stage is to be baselined |
| 2 Decisions | 4 | Retire filter, RP-112, press A on a retirement, then Ctrl+K, CC-003, A | Routine items are seeded as earlier work, and the app shows them as accepted in an earlier session. The audit pack looks unused, and the system refused to retire it. A retirement waits for the customer |
| 3 Custom code | 4 | CC-014: summary, embedded rule, conflict, Run live, spec, tests | Direct database writes cannot move to Unit4 cloud. 10% in code, 15% in policy: the customer decides. The extension spec is illustrative until Unit4 confirms it |
| 4 Reports | 3 | Reduction, rebuild, fix the list | Rebuilt faithfully, totals match to the penny. Fixed, the difference is exactly the omitted partners' WIP |
| 5 Workflows | 2 | Usage, proposal, send pack | Two variants handle 94% of approvals. Controls are the customer's call |
| 6 Reconcile | 4 | Run, R2, R4, R6, then threshold and run again | Plain code, no language model. Open R2 and show the proven cause. Ask the customer, switch to Jordan, choose, switch back, run again. Run once more to show the identical result |
| 7 Sign-off pack | 1 | Answer customer questions in the console, generate, switch to Jordan, sign | This accepts a trial migration with listed exceptions. It is not cutover. Undecided items remain, and those marked as accepted in earlier sessions are seeded history |
| 8 Results | 1 | Scorecard | Ten of ten on synthetic data, against an answer key, which the screen calls known issues and expected results. We quote no percentage saving, because Unit4 has shared no baseline |

Scene 7 needs five customer questions answered first: the four seeded ones plus the workflow pack. Press **Answer customer questions** in the console, which keeps the run so far, or switch to Jordan and answer one or two aloud. Answering all five by hand does not fit the 1-minute budget.

**Live agents.** `.env` must hold `ANTHROPIC_API_KEY`, and the button shows only for Robin. On the Code screen, press **Run live** on the explanation panel as the visible AI moment, or on the workflow proposal. A run can take a minute, so talk through it. The badge changes to AI analysis only when a model wrote the result. If a run fails, the cached result stays and a message says so. **Reset** restores the cached results.

**What does what.** The ontology is the shared meaning: agents are grounded in it, and the decision rules read its protected purposes. AI agents read code and draft. Decision rules are plain code, not a trained model. Reconciliation is plain code. People decide. The ontology has 25 concepts in plain terms, pending the specialist's review, so do not present it as a full CR and ERPx model.

Optional if a scene runs short, each about 20 seconds:

- **Code:** open the Skeleton tab. It is a starting point for review, and the API names need Unit4 to confirm them. The Ava note below the panels is an idea only.
- **Workflows:** open the one-page decision pack.
- **Reconcile:** open R6 and approve the duplicate value as Robin. It applies at the next trial load, so the check still fails until then.
- **Results:** show consultant effort by case, and mapping memory after an edit in Decisions. Memory matches exact patterns, and with one customer it can only preview the next proposal.

## If something goes wrong

| Problem | Do this |
|---|---|
| A scene stalls | **Play recording**, keep talking, then **Back to live** |
| The API is not responding | The register offers Try again. Otherwise continue from recordings |
| The state looks wrong | **Prepare scene N** for the current scene |
| A question from Unit4 on CR detail | Say the estate is synthetic and our specialist reviews it. Note it for the open-questions list |

## What we do not claim

- No time savings or accuracy figures that apply to real customers.
- The agent does not decide. Every decision needs a consultant, and every retirement needs the customer.
- No cutover readiness. Parallel runs and cutover need Unit4 and customer approval.
- Prepared analysis is written by hand. Only a result marked AI analysis came from a model, and a person still reviews it.
