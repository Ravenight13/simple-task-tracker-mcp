import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  timeout: 30000,
  use: {
    headless: false,
    screenshot: 'on',
    video: 'retain-on-failure',
    baseURL: 'http://localhost:8001',
  },
  reporter: 'list',
});
