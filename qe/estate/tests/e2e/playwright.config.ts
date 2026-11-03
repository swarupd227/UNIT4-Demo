import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './specs',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: Number(process.env.WORKERS ?? 2),
  retries: Number(process.env.RETRIES ?? 0),
  reporter: process.env.CI
    ? [['list'], ['junit', { outputFile: 'results/junit.xml' }]]
    : [['list']],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:5280',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
