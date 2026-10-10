const { defineConfig } = require("@playwright/test");

const baseURL = process.env.BASE_URL || "http://127.0.0.1:8000";
const usesExternalServer = Boolean(process.env.BASE_URL);

module.exports = defineConfig({
  testDir: "./tests/responsive",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
    toHaveScreenshot: { maxDiffPixelRatio: 0.01 },
  },
  forbidOnly: Boolean(process.env.CI),
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: usesExternalServer
    ? undefined
    : {
        command: "python3 manage.py runserver 127.0.0.1:8000 --noreload",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      },
  projects: [
    { name: "phone-small", use: { browserName: "chromium", viewport: { width: 390, height: 844 } } },
    { name: "phone-large", use: { browserName: "chromium", viewport: { width: 430, height: 932 } } },
    { name: "tablet", use: { browserName: "chromium", viewport: { width: 768, height: 1024 } } },
    { name: "laptop", use: { browserName: "chromium", viewport: { width: 1366, height: 768 } } },
    { name: "desktop", use: { browserName: "chromium", viewport: { width: 1440, height: 900 } } },
    { name: "safari-phone", use: { browserName: "webkit", viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
});
