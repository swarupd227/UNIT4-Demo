import { expect, test, type Page } from "@playwright/test";
import { asPerson } from "./helpers";

// One continuous run in script order, with no scene preparation and real model calls.
// Costs money, so it runs only with REHEARSAL=1.
test.skip(!process.env.REHEARSAL, "Set REHEARSAL=1 to rehearse");
test.setTimeout(600_000);

const LIVE_LIMIT_MS = 110_000;
const SCREEN_LIMIT_MS = 15_000;

async function shot(page: Page, name: string) {
  await page.waitForTimeout(900);
  await page.screenshot({ path: `e2e-results/rehearsal/${name}.png` });
}

async function nextScene(page: Page) {
  await page.mouse.click(5, 300);
  await page.keyboard.press("ArrowRight");
}

async function runLive(page: Page, label: string) {
  const started = Date.now();
  await page.getByRole("button", { name: "Run live" }).click();
  await expect(page.getByText("AI analysis").first()).toBeVisible({ timeout: LIVE_LIMIT_MS });
  await expect(page.getByRole("button", { name: "Run live" })).toBeVisible({ timeout: LIVE_LIMIT_MS });
  console.log(`LIVE ${label} ${((Date.now() - started) / 1000).toFixed(1)}s`);
}

test("full rehearsal in script order", async ({ page, request }) => {
  page.setDefaultTimeout(30_000);
  const errors: string[] = [];
  page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
  page.on("pageerror", (error) => errors.push(error.message));
  const marks: [string, number][] = [];
  const mark = (scene: string) => marks.push([scene, Date.now()]);

  expect((await request.post("/api/workspace/reset")).ok()).toBeTruthy();
  const started = Date.now();

  mark("0 Set the scene");
  await page.goto("/customer");
  await expect(page.getByText("Sandbox environment")).toBeVisible();
  await expect(page.locator("header").first()).toContainText("82 of 233");
  await shot(page, "00-customer");

  mark("1 Load the estate");
  await nextScene(page);
  await expect(page.getByRole("heading", { name: "CR estate" })).toBeVisible();
  await shot(page, "01-estate-start");
  await page.getByRole("button", { name: "Load estate" }).click();
  await expect(page.getByText("Estate map")).toBeVisible({ timeout: SCREEN_LIMIT_MS });
  await shot(page, "02-estate-loaded");

  mark("2 Decisions");
  await nextScene(page);
  await expect(page.getByRole("heading", { name: "Decision register" })).toBeVisible();
  await page.getByRole("row", { name: /RP-112/ }).click();
  const panel = page.getByRole("complementary", { name: "Item detail" });
  await expect(panel.getByText("Retirement blocked")).toBeVisible();
  await shot(page, "03-decisions-rp112");
  await panel.getByRole("button", { name: /Protected word/ }).click();
  await expect(page.getByRole("dialog")).toContainText("never retired");
  await shot(page, "04-decisions-evidence");
  await page.keyboard.press("Escape");
  await page.getByRole("row", { name: /To review/ }).first().click();
  await expect(panel.getByRole("button", { name: /^Accept/ })).toBeEnabled();
  await page.keyboard.press("a");
  await expect(panel.getByText("Waiting for the customer.")).toBeVisible();
  await page.keyboard.press("Control+k");
  await page.getByPlaceholder("Find an item by ID or name").fill("CC-003");
  await page.keyboard.press("Enter");
  await expect(panel.getByRole("heading", { name: "Purchase order number sequence" })).toBeVisible();
  await expect(panel.getByRole("button", { name: /^Accept/ })).toBeEnabled();
  await page.keyboard.press("a");
  await expect(page.locator("header").first()).toContainText("83 of 233");
  await shot(page, "05-decisions-accepted");

  mark("3 Custom code");
  await nextScene(page);
  await expect(page.getByText("Billing adjust writer").first()).toBeVisible();
  await page.getByRole("button", { name: /Write-downs above 10%/ }).hover();
  await shot(page, "06-code-rule-line");
  await runLive(page, "code explainer");
  await shot(page, "07-code-live");
  await page.getByRole("tab", { name: "Extension spec" }).click();
  await shot(page, "08-code-spec");
  await page.getByRole("tab", { name: "Skeleton" }).click();
  await shot(page, "09-code-skeleton");
  await page.getByRole("tab", { name: "Tests" }).click();
  await shot(page, "10-code-tests");

  mark("4 Reports");
  await nextScene(page);
  await expect(page.getByText("148 in scope")).toBeVisible();
  await shot(page, "11-reports");
  await page.getByRole("button", { name: "Rebuild and run parity" }).click();
  await expect(page.getByText("Totals match to the penny")).toBeVisible();
  await page.getByRole("button", { name: "Fix the partner list" }).click();
  await expect(page.getByText("equals the WIP of P041")).toBeVisible();
  await shot(page, "12-reports-parity");

  mark("5 Workflows");
  await nextScene(page);
  await expect(page.getByText("9 variants")).toBeVisible();
  await shot(page, "13-workflows");
  await page.getByRole("button", { name: "View proposal" }).click();
  await expect(page.getByRole("heading", { name: "Control impact" })).toBeVisible();
  await shot(page, "14-workflows-proposal");
  await runLive(page, "workflow pack");
  await shot(page, "15-workflows-live");
  const pack = await request.get("/api/workflows/decision-pack.pdf");
  expect(pack.ok()).toBeTruthy();
  await page.getByRole("button", { name: "Send pack to customer" }).click();
  await expect(page.getByRole("button", { name: "Sent to the customer" })).toBeVisible();

  mark("6 Reconcile");
  await nextScene(page);
  await page.getByRole("button", { name: "Run the checks" }).click();
  await expect(page.getByText("4 of 8").first()).toBeVisible({ timeout: SCREEN_LIMIT_MS });
  await shot(page, "16-reconcile");
  for (const check of ["R2", "R4", "R6"]) {
    await page.getByRole("button", { name: new RegExp(`^${check}`) }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await shot(page, `17-reconcile-${check}`);
    if (check !== "R6") await page.keyboard.press("Escape");
  }
  await page.getByRole("dialog").getByRole("button", { name: "Approve proposed action" }).click();
  await expect(page.getByRole("dialog")).toContainText("Applies at the next trial load");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Ask the customer" }).click();
  await expect(page.getByText("Waiting for Jordan Ashby")).toBeVisible();
  await asPerson(page, "Robin Hale", "Jordan Ashby");
  await page.getByRole("button", { name: /^15%/ }).click();
  await expect(page.getByText("Threshold chosen")).toBeVisible();
  await asPerson(page, "Jordan Ashby", "Robin Hale");
  await page.getByRole("button", { name: "Run again" }).first().click();
  await expect(page.getByText("9 tests pass at 15%")).toBeVisible({ timeout: SCREEN_LIMIT_MS });
  await page.getByRole("button", { name: "Run again" }).first().click();
  await expect(page.getByText(/Run again, identical result/)).toBeVisible({ timeout: SCREEN_LIMIT_MS });
  await shot(page, "18-reconcile-final");

  mark("7 Sign-off pack");
  await nextScene(page);
  await expect(page.getByRole("heading", { name: "Customer sign-off" })).toBeVisible();
  await shot(page, "19-signoff-start");
  const presenter = await page.context().newPage();
  await presenter.goto("/presenter");
  await presenter.getByRole("button", { name: "Answer customer questions" }).click();
  await expect(page.getByText("None open")).toBeVisible();
  await presenter.close();
  await shot(page, "20-signoff-cleared");
  await page.getByRole("button", { name: "Generate the pack" }).click();
  await expect(page.frameLocator('iframe[title="Sign-off pack"]').getByText("Customer sign-off pack")).toBeVisible({
    timeout: SCREEN_LIMIT_MS,
  });
  await shot(page, "21-signoff-pack");
  await asPerson(page, "Robin Hale", "Jordan Ashby");
  await page.getByRole("button", { name: "Sign off the trial migration" }).click();
  await expect(page.getByText(/Signed by Jordan Ashby/)).toBeVisible();
  await shot(page, "22-signoff-signed");

  mark("8 Results");
  await asPerson(page, "Jordan Ashby", "Robin Hale");
  await nextScene(page);
  await expect(page.getByText("Known issues found")).toBeVisible();
  await shot(page, "23-results");
  await page.getByRole("heading", { name: "Mapping memory" }).scrollIntoViewIfNeeded();
  await shot(page, "24-results-lower");

  mark("End");
  marks.slice(0, -1).forEach(([scene, at], index) => {
    console.log(`SCENE ${scene}: ${((marks[index + 1][1] - at) / 1000).toFixed(1)}s`);
  });
  console.log(`TOTAL ${((Date.now() - started) / 1000).toFixed(1)}s`);
  console.log(`CONSOLE ERRORS ${JSON.stringify(errors)}`);
  const score = await (await request.get("/api/scorecard")).json();
  console.log(`SCORE ${score.found} of ${score.planted}, false ${score.false_items.count}, decisions ${score.decision_quality.matched} of ${score.decision_quality.total}, passed ${score.passed}`);
  console.log(`AGENTS ${JSON.stringify(score.artefacts)}`);
  expect(errors).toEqual([]);
});
