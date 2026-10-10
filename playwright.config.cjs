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
    {
      name: "iphone-16-pro",
      use: {
        browserName: "webkit",
        viewport: { width: 402, height: 874 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "oppo-a96-cph2333",
      use: {
        browserName: "chromium",
        viewport: { width: 360, height: 804 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true,
      },
    },
    { name: "tablet", use: { browserName: "chromium", viewport: { width: 768, height: 1024 } } },
    {
      name: "ipad-mini-a17-pro",
      use: {
        browserName: "webkit",
        viewport: { width: 744, height: 1133 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
      },
    },
    { name: "laptop", use: { browserName: "chromium", viewport: { width: 1366, height: 768 } } },
    {
      name: "macbook-pro-16-2019",
      use: {
        browserName: "chromium",
        viewport: { width: 1536, height: 960 },
        deviceScaleFactor: 2,
      },
    },
    { name: "desktop", use: { browserName: "chromium", viewport: { width: 1440, height: 900 } } },
    { name: "safari-phone", use: { browserName: "webkit", viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
});
