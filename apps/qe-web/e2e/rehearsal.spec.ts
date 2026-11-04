import { copyFileSync, mkdirSync } from "node:fs";
import { expect, test, type Page, type TestInfo } from "@playwright/test";

// The whole journey in script order, on real data and the real lab, one test per scene. The scenes share
// the workbench's state, so they run in order after one reset. With RECORD=1 each scene's video is kept
// as that scene's fallback recording for the presenter console.
test.describe.configure({ mode: "serial" });

const SCENE_LOAD_MS = 2_000;
const LIVE_CHECK_MS = 120_000;
const FALLBACK = "/workspace/apps/qe-web/public/fallback";

async function as(page: Page, role: "qe_lead" | "engineer") {
  await page.addInitScript((r) => localStorage.setItem("assurance.persona", r), role);
}

const STAGE_LABELS: Record<string, string> = {
  "/area": "Area",
  "/coverage": "Coverage",
  "/context": "Context",
  "/tests": "Generated tests",
  "/proof": "Proof",
  "/flaky": "Flaky tests",
  "/review": "Pull request",
  "/gaps": "Gaps",
  "/scorecard": "Scorecard",
};

// Opens a scene the way the presenter does, from the stage rail of an app that is already open, and
// checks it is ready to talk over within the limit. Loading the app itself is not part of a scene.
async function open(page: Page, path: string, ready: RegExp | string) {
  await page.goto(path === "/area" ? "/coverage" : "/area");
  await expect(page.getByRole("navigation", { name: "Stages" })).toBeVisible();
  const started = Date.now();
  await page.getByRole("navigation", { name: "Stages" }).getByRole("link", { name: STAGE_LABELS[path] }).click();
  await expect(page.getByText(ready).first()).toBeVisible();
  const ms = Date.now() - started;
  console.log(`SCENE ${path} ready in ${ms} ms`);
  // Encoding video slows the browser, so a recording run keeps the fallbacks and does not time scenes.
  if (!process.env.RECORD) expect(ms, `${path} took ${ms} ms`).toBeLessThan(SCENE_LOAD_MS);
}

async function keep(page: Page, info: TestInfo, scene: number) {
  if (!process.env.RECORD) return;
  const video = page.video();
  await page.close();
  if (video) {
    mkdirSync(FALLBACK, { recursive: true });
    copyFileSync(await video.path(), `${FALLBACK}/scene-${scene}.webm`);
  }
  info.annotations.push({ type: "fallback", description: `scene-${scene}.webm` });
}

test.beforeAll(async ({ request }) => {
  test.setTimeout(300_000);
  const reset = await request.post("/api/workspace/reset", { timeout: 240_000 });
  expect(reset.ok()).toBeTruthy();
});

test("0 Set the scene", async ({ page }, info) => {
  await open(page, "/area", "Estate");
  await expect(page.getByText("Sandbox")).toBeVisible();
  await expect(page.getByText("business rules, 12 critical")).toBeVisible();
  await page.waitForTimeout(1500);
  await keep(page, info, 0);
});

test("1 Coverage map", async ({ page }, info) => {
  await open(page, "/coverage", "7 of 12 critical rules covered (58%)");
  await expect(page.getByText("No automated test names this rule.")).toBeVisible();
  await page.getByRole("button", { name: /BR-11/ }).click();
  await expect(page.getByText("Weak test").first()).toBeVisible();
  await page.waitForTimeout(1500);
  await keep(page, info, 1);
});

test("2 Context", async ({ page }, info) => {
  await as(page, "engineer");
  await open(page, "/context", "Multi-currency rounding");
  await expect(page.getByText("fixed with no test at all").first()).toBeVisible();
  await page.getByRole("button", { name: "Approve", exact: true }).first().click();
  await expect(page.getByText(/approved$/).first()).toBeVisible();
  await page.getByRole("tab", { name: /Hidden rules/ }).click();
  await expect(page.getByText("Found in code only.").first()).toBeVisible();
  await page.getByRole("button", { name: "Approve", exact: true }).first().click();
  await expect(page.getByText(/Approved by Ravi Menon/).first()).toBeVisible();
  await page.waitForTimeout(1500);
  await keep(page, info, 2);
});

test("3 Generate", async ({ page }, info) => {
  await open(page, "/tests", "Manual case intake");
  await expect(page.getByText("Sent to a person").first()).toBeVisible();
  await expect(page.getByText("Expected result needed").first()).toBeVisible();
  await expect(page.getByText("Merged", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Passed all four checks")).toHaveCount(10);
  await page.waitForTimeout(1500);
  await keep(page, info, 3);
});

test("4 Prove tests", async ({ page }, info) => {
  test.setTimeout(LIVE_CHECK_MS + 60_000);
  await open(page, "/proof", "9 of 12 (75%)");
  await expect(page.getByText(/case 48224/).first()).toBeVisible();
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByText("Caught.")).toBeVisible({ timeout: LIVE_CHECK_MS });
  await page.waitForTimeout(1500);
  await keep(page, info, 4);
});

test("5 Flaky tests", async ({ page }, info) => {
  await as(page, "engineer");
  await open(page, "/flaky", "Flaky tests and maintenance");
  await expect(page.getByText("0 of 20")).toHaveCount(2);
  await expect(page.getByText("Next release: release-4.9")).toBeVisible();
  await page.waitForTimeout(1500);
  await keep(page, info, 5);
});

test("6 Engineer review", async ({ page }, info) => {
  await as(page, "engineer");
  await open(page, "/review", "Release controls unchanged");
  const items = page.getByRole("region", { name: "Pull request" }).locator("li button");
  const count = await items.count();
  expect(count).toBe(12);
  for (let i = 0; i < count; i++) {
    await items.nth(i).click();
    await page.getByRole("button", { name: "Approve", exact: true }).click();
    await expect(items.nth(i).getByLabel("Approved")).toBeVisible();
  }
  await page.getByRole("button", { name: "Merge approved items" }).click();
  await expect(page.getByText(/Merged by Ravi Menon/)).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(1500);
  await keep(page, info, 6);
});

test("7 Gaps and pack", async ({ page }, info) => {
  await open(page, "/gaps", "Rules below the gate");
  for (const rule of ["BR-11", "BR-15", "BR-19"]) await expect(page.getByText(rule).first()).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Evidence pack" }).click();
  expect((await download).suggestedFilename()).toBe("project-billing-evidence-pack.json");
  await page.waitForTimeout(1500);
  await keep(page, info, 7);
});

test("8 Results", async ({ page }, info) => {
  await open(page, "/scorecard", "Meaningful coverage");
  await expect(page.getByText("9 of 12 (75%)")).toBeVisible();
  await expect(page.getByLabel("Handled as expected")).toHaveCount(10);
  await expect(page.getByText(/Merged by Ravi Menon/)).toBeVisible();
  await page.waitForTimeout(1500);
  await keep(page, info, 8);
});
