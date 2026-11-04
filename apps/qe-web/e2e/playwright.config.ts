import { defineConfig, devices } from "@playwright/test";

// The rehearsal of the whole journey. Runs in the lab image, which already has Playwright and its
// browsers: npm run qe:rehearse (and npm run qe:record-fallbacks to keep each scene's video).
export default defineConfig({
  testDir: ".",
  timeout: 180_000,
  expect: { timeout: 15_000 },
  workers: 1,
  retries: 0,
  outputDir: "/workspace/apps/qe-web/e2e-results",
  reporter: [["list"]],
  use: {
    baseURL: process.env.APP_URL ?? "http://qe-web:5193",
    viewport: { width: 1600, height: 1000 },
    locale: "en-GB",
    video: process.env.RECORD ? { mode: "on", size: { width: 1600, height: 1000 } } : "off",
    // Tracing snapshots every action and slows the browser, so it is opt-in: TRACE=1.
    trace: process.env.TRACE ? "retain-on-failure" : "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } } }],
});
