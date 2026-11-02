import { expect, test } from "@playwright/test";
import { asPerson, failOnConsoleErrors, prepare, timedGoto } from "./helpers";

let checkConsole: () => void;

test.beforeEach(async ({ page }) => {
  checkConsole = failOnConsoleErrors(page);
});

test.afterEach(async ({ page }, info) => {
  checkConsole();
  const video = page.video();
  if (!video) return;
  const scene = info.title.match(/^scene (\d)/)?.[1];
  await page.close();
  // saveAs waits for the recording to finish. Copying the file straight after close does not.
  if (scene) await video.saveAs(`public/fallback/scene-${scene}.webm`);
});

test("scene 0 sets the scene", async ({ page, request }) => {
  await prepare(request, 0);
  await timedGoto(page, "/customer", "Sandbox environment");
  await expect(page.getByText("Custom reports")).toBeVisible();
  await page.waitForTimeout(700);
  const tile = page.getByText("148", { exact: true }).locator("..");
  await expect(tile).toHaveCSS("opacity", "1");
  await page.waitForTimeout(2500);
});

test("scene 1 loads the estate on top of J2X", async ({ page, request }) => {
  await prepare(request, 1);
  await timedGoto(page, "/estate", "CR estate");
  await page.getByRole("button", { name: "Load estate" }).click();
  await expect(page.getByText("Estate map")).toBeVisible();
  await expect(page.getByText("107 of 148 explained")).toBeVisible();
  await page.waitForTimeout(2500);
});

test("scene 2 refuses to retire the audit pack", async ({ page, request }) => {
  await prepare(request, 2);
  await timedGoto(page, "/decisions?outcome=retire", "Decision register");
  await page.getByRole("row", { name: /RP-112/ }).click();
  const panel = page.getByRole("complementary", { name: "Item detail" });
  await expect(panel.getByRole("heading", { name: "Year-end audit pack" })).toBeVisible();
  await expect(panel.getByText("Retirement blocked")).toBeVisible();
  await panel.getByRole("button", { name: /Protected word/ }).click();
  await expect(page.getByRole("dialog")).toContainText("never retired");
  await page.waitForTimeout(1500);
  await page.keyboard.press("Escape");
  await page.getByRole("row", { name: /To review/ }).first().click();
  await expect(panel.getByRole("button", { name: /^Accept/ })).toBeEnabled();
  await page.keyboard.press("a");
  await expect(panel.getByText("Waiting for the customer.")).toBeVisible();
  await page.waitForTimeout(1500);
});

test("scene 3 explains CC-014", async ({ page, request }) => {
  await prepare(request, 3);
  await timedGoto(page, "/code/CC-014", "Billing adjust writer");
  await page.getByRole("button", { name: /Write-downs above 10%/ }).hover();
  await expect(page.getByText("private const decimal Limit").locator("xpath=ancestor::div[1]")).toBeVisible();
  await expect(page.getByText("INT-09 also writes zz_rate_override")).toBeVisible();
  await expect(page.getByText("Grounded in the ontology:")).toBeVisible();
  await page.getByRole("tab", { name: "Extension spec" }).click();
  await expect(page.getByText("Write-down approval", { exact: false }).first()).toBeVisible();
  await page.waitForTimeout(1000);
  await page.getByRole("tab", { name: "Skeleton" }).click();
  await expect(page.getByText("public sealed class WriteDownApproval")).toBeVisible();
  await page.getByRole("tab", { name: "Tests" }).click();
  await expect(page.getByText("where the two thresholds disagree")).toBeVisible();
  await expect(page.getByText("Idea only")).toBeVisible();
  await page.waitForTimeout(1500);
});

test("scene 4 proves the rebuild to the penny", async ({ page, request }) => {
  await prepare(request, 4);
  await timedGoto(page, "/reports", "148 in scope");
  await page.waitForTimeout(1300);
  await page.getByRole("button", { name: "Rebuild and run parity" }).click();
  await expect(page.getByText("Totals match to the penny")).toBeVisible();
  await page.waitForTimeout(1000);
  await page.getByRole("button", { name: "Fix the partner list" }).click();
  await expect(page.getByText("equals the WIP of P041")).toBeVisible();
  await expect(page.getByText("£4,583,872.60").first()).toBeVisible();
  await page.waitForTimeout(1500);
});

test("scene 5 moves nine workflows to three", async ({ page, request }) => {
  await prepare(request, 5);
  await timedGoto(page, "/workflows", "9 variants");
  await page.getByRole("button", { name: "View proposal" }).click();
  await expect(page.getByText("Used only by a dormant legal entity")).toBeVisible();
  await expect(page.getByText("Two steps: line manager, budget holder")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Test cases" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open decision pack" })).toHaveAttribute(
    "href",
    "/api/workflows/decision-pack.pdf",
  );
  await page.getByRole("button", { name: "Send pack to customer" }).click();
  await expect(page.getByRole("button", { name: "Sent to the customer" })).toBeVisible();
  await page.waitForTimeout(1500);
});

test("scene 6 reconciles and proves determinism", async ({ page, request }) => {
  await prepare(request, 6);
  await timedGoto(page, "/reconcile", "Reconciliation");
  await page.getByRole("button", { name: "Run the checks" }).click();
  await expect(page.getByText("4 of 8").first()).toBeVisible({ timeout: 15_000 });
  await page.getByRole("button", { name: /^R2/ }).click();
  await expect(page.getByRole("dialog")).toContainText("reproduces the difference exactly");
  await page.waitForTimeout(1500);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Ask the customer" }).click();
  await expect(page.getByText("Waiting for Jordan Ashby")).toBeVisible();
  await asPerson(page, "Robin Hale", "Jordan Ashby");
  await page.getByRole("button", { name: /^15%/ }).click();
  await expect(page.getByText("Threshold chosen")).toBeVisible();
  await asPerson(page, "Jordan Ashby", "Robin Hale");
  await page.getByRole("button", { name: "Run again" }).first().click();
  await expect(page.getByText("9 tests pass at 15%")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("5 of 8").first()).toBeVisible();
  await page.getByRole("button", { name: "Run again" }).first().click();
  await expect(page.getByText(/Run again, identical result/)).toBeVisible({ timeout: 15_000 });
  await page.getByRole("button", { name: /^R6/ }).click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toContainText("Waiting for Jordan Ashby.");
  await drawer.getByRole("button", { name: "Approve proposed action" }).click();
  await expect(drawer).toContainText("Applies at the next trial load");
  await page.waitForTimeout(1500);
});

test("the customer can answer every kind of question", async ({ page, request }) => {
  await prepare(request, 6);
  await page.addInitScript(() => localStorage.setItem("studio.persona", "customer"));
  await page.goto("/signoff");
  await expect(page.getByText("4 customer questions open")).toBeVisible();
  await page.getByRole("button", { name: "Retire it" }).first().click();
  await expect(page.getByText("3 customer questions open")).toBeVisible();
  await page.getByRole("button", { name: "Keep it" }).first().click();
  await expect(page.getByText("2 customer questions open")).toBeVisible();
  await page.getByLabel("Your answer").fill("Ask the finance systems lead");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("1 customer questions open")).toBeVisible();
});

test("scene 7 generates and signs the pack", async ({ page, request }) => {
  await prepare(request, 7);
  await timedGoto(page, "/signoff", "Customer sign-off");
  const started = Date.now();
  await page.getByRole("button", { name: "Generate the pack" }).click();
  await expect(page.frameLocator('iframe[title="Sign-off pack"]').getByText("Customer sign-off pack")).toBeVisible();
  console.log(`PACK generated in ${Date.now() - started}ms`);
  await expect(page.getByText("Of which accepted in earlier sessions")).toBeVisible();
  await page.waitForTimeout(1000);
  await asPerson(page, "Robin Hale", "Jordan Ashby");
  await page.getByRole("button", { name: "Sign off the trial migration" }).click();
  await expect(page.getByText(/Signed by Jordan Ashby/)).toBeVisible();
  await page.waitForTimeout(1500);
});

test("scene 8 shows measured results and no saving", async ({ page, request }) => {
  await prepare(request, 8);
  await timedGoto(page, "/scorecard", "Known issues found");
  await expect(page.getByText("No baseline available")).toBeVisible();
  await expect(page.getByText("Signed by the customer")).toBeVisible();
  await expect(page.getByText("Case 2: report estate")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Mapping memory" })).toBeVisible();
  await expect(page.getByLabel("Not found yet")).toHaveCount(0);
  await page.waitForTimeout(2500);
});

test("the presenter console drives the audience window", async ({ context, request }) => {
  await prepare(request, 0);
  const audience = await context.newPage();
  await audience.goto("/customer");
  await expect(audience.getByText("Sandbox environment")).toBeVisible();
  const consoleWindow = await context.newPage();
  await consoleWindow.goto("/presenter");
  await consoleWindow.getByRole("button", { name: /Next: Load the estate/ }).click();
  await expect(audience.getByText("CR estate")).toBeVisible();
  await consoleWindow.keyboard.press("ArrowRight");
  await expect(audience).toHaveURL(/decisions/);
  await expect(audience).toHaveURL(/decisions\/[A-Z]/);
  await audience.keyboard.press("ArrowRight");
  await expect(audience).toHaveURL(/code\/CC-014/);
  await expect(consoleWindow.getByRole("heading", { name: /Custom code/ })).toBeVisible();
  await expect(audience.getByText("Say plainly")).toHaveCount(0);
  await consoleWindow.getByRole("button", { name: /Reset/ }).click();
  await expect(audience).toHaveURL(/customer/);
  await audience.close();
  await consoleWindow.close();
});

test("reduced motion still shows everything", async ({ browser, baseURL, request }) => {
  await prepare(request, 0);
  const context = await browser.newContext({ reducedMotion: "reduce", baseURL, viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  await page.goto("/customer");
  await expect(page.getByText("Custom reports")).toBeVisible();
  await page.waitForTimeout(600);
  await expect(page.getByText("148", { exact: true }).locator("..")).toHaveCSS("opacity", "1");
  await context.close();
});

test("reset is quick", async ({ request }) => {
  const started = Date.now();
  const response = await request.post("/api/workspace/reset");
  expect(response.ok()).toBeTruthy();
  const elapsed = Date.now() - started;
  console.log(`RESET ${elapsed}ms`);
  expect(elapsed).toBeLessThan(2000);
});

test("a recording plays over the app and returns to live", async ({ context, request }) => {
  test.skip(Boolean(process.env.RECORD), "Recordings do not exist yet during a recording run");
  await prepare(request, 0);
  const audience = await context.newPage();
  await audience.goto("/customer");
  await expect(audience.getByText("Sandbox environment")).toBeVisible();
  const consoleWindow = await context.newPage();
  await consoleWindow.goto("/presenter");
  await consoleWindow.getByRole("button", { name: "Play recording" }).click();
  const video = audience.locator("video");
  await expect(video).toBeVisible();
  await expect
    .poll(() => video.evaluate((element: HTMLVideoElement) => [element.error, element.duration > 1]))
    .toEqual([null, true]);
  await consoleWindow.getByRole("button", { name: "Back to live" }).click();
  await expect(video).toHaveCount(0);
  await audience.close();
  await consoleWindow.close();
});
