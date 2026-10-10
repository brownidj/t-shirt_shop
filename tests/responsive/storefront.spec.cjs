const { test, expect } = require("@playwright/test");

const pages = [
  ["home", "/"],
  ["catalogue", "/catalogue/"],
  ["login", "/accounts/login/"],
  ["design-request", "/request-a-design/"],
  ["basket", "/basket/"],
];

// The carousel and catalogue rotate content as they load, so a full-page
// pixel comparison would create false failures.  They still receive the
// viewport-overflow check below.
const visualPages = new Set(["login", "design-request", "basket"]);

async function expectNoHorizontalOverflow(page) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

for (const [name, path] of pages) {
  test(`${name} fits its viewport`, async ({ page }) => {
    await page.goto(path, { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
    await expectNoHorizontalOverflow(page);

    if (!process.env.LIVE_SMOKE && visualPages.has(name)) {
      await expect(page).toHaveScreenshot(`${name}.png`, {
        animations: "disabled",
        fullPage: true,
      });
    }
  });
}

test("signed-in wishlist can be inspected without changing it", async ({ page }, testInfo) => {
  test.skip(
    !process.env.RESPONSIVE_TEST_USERNAME || !process.env.RESPONSIVE_TEST_PASSWORD,
    "Set responsive test credentials to include the signed-in wishlist."
  );

  await page.goto("/accounts/login/", { waitUntil: "domcontentloaded" });
  await page.locator('input[name="username"]').fill(process.env.RESPONSIVE_TEST_USERNAME);
  await page.locator('input[name="password"]').fill(process.env.RESPONSIVE_TEST_PASSWORD);
  await page.locator('button[type="submit"]').click();
  await page.goto("/wishlist/", { waitUntil: "domcontentloaded" });

  await expectNoHorizontalOverflow(page);
  await expect(page.locator(".wishlist-quantity-stepper").first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("wishlist.png"), fullPage: true });
});
