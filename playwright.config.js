import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './',
  testMatch: 'test-task-viewer-verification.js',
  timeout: 30000,
  use: {
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  reporter: 'list',
});
