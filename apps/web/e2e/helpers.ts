import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const SCENE_LOAD_LIMIT_MS = 2000;

export async function prepare(request: APIRequestContext, scene: number) {
  const response = await request.post(`/api/workspace/prepare/${scene}`);
  expect(response.ok()).toBeTruthy();
}

export async function asPerson(page: Page, current: string, next: string) {
  await page.getByRole("button", { name: new RegExp(current) }).click();
  await page.getByRole("menuitem", { name: new RegExp(next) }).click();
  await expect(page.locator("header").getByText(next)).toBeVisible();
}

// Every load is timed from navigation until the screen's real content is on show.
export async function timedGoto(page: Page, path: string, ready: string) {
  const started = Date.now();
  await page.goto(path);
  await expect(page.getByText(ready, { exact: false }).first()).toBeVisible();
  const elapsed = Date.now() - started;
  console.log(`LOAD ${path} ${elapsed}ms`);
  // Encoding video slows the page, and the audience never sees that, so recorded runs are not timed.
  if (!process.env.RECORD) expect(elapsed).toBeLessThan(SCENE_LOAD_LIMIT_MS);
}

export function failOnConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return () => expect(errors).toEqual([]);
}
