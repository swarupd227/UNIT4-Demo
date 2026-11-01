import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { prepare } from "./helpers";

const SCREENS: [string, string, string][] = [
  ["Customer", "/customer", "Sandbox environment"],
  ["Estate", "/estate", "CR estate"],
  ["Decisions", "/decisions/CC-014", "Billing adjust writer"],
  ["Code", "/code/CC-014", "Explanation"],
  ["Reports", "/reports", "148 in scope"],
  ["Workflows", "/workflows", "Use in the last 12 months"],
  ["Reconcile", "/reconcile", "Report parity"],
  ["Sign-off", "/signoff", "Before signing"],
  ["Scorecard", "/scorecard", "Known issues found"],
  ["Presenter", "/presenter", "Rehearsals"],
];

async function audit(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  return results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    count: violation.nodes.length,
    example: violation.nodes[0]?.html.slice(0, 120),
    summary: violation.nodes[0]?.failureSummary?.split("\n")[1]?.trim().slice(0, 140),
  }));
}

test.beforeAll(async ({ request }) => {
  await prepare(request, 8);
});

for (const [name, path, ready] of SCREENS) {
  test(`${name} meets WCAG 2.2 AA`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByText(ready).first()).toBeVisible();
    await page.waitForTimeout(1200);
    const violations = await audit(page);
    if (violations.length) console.log(`AXE ${name} ${JSON.stringify(violations)}`);
    expect(violations.filter((v) => v.impact === "critical" || v.impact === "serious")).toEqual([]);
  });
}

test("the decision flow works by keyboard alone", async ({ page, request }) => {
  await prepare(request, 2);
  await page.goto("/decisions/CC-029");
  await expect(page.getByRole("heading", { name: "Project closure checklist v1" })).toBeVisible();
  await expect(page.getByRole("row", { name: /CC-029/ })).toBeVisible();
  await page.keyboard.press("j");
  await page.keyboard.press("k");
  await expect(page).toHaveURL(/CC-029/);
  await page.keyboard.press("e");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.keyboard.press("a");
  await expect(page.getByText("Waiting for the customer.")).toBeVisible();
  await page.keyboard.press("Control+k");
  await page.keyboard.type("year-end");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/RP-112/);
});
