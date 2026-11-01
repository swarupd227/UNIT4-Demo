import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e-results",
  workers: 1,
  timeout: 60_000,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5184",
    viewport: { width: 1920, height: 1080 },
    locale: "en-GB",
    video: process.env.RECORD ? { mode: "on", size: { width: 1920, height: 1080 } } : "off",
  },
});
