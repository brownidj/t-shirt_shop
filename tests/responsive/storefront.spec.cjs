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

async function visitDescribedDesign(page) {
  await page.goto("/catalogue/", { waitUntil: "domcontentloaded" });
  const designLink = page.locator('a[href*="/catalogue/cambroernid-02_"]').first();
  await expect(designLink).toBeVisible();
  const href = await designLink.getAttribute("href");
  if (!href) {
    throw new Error("Cambroernid 02 catalogue link has no destination");
  }
  await page.goto(href, { waitUntil: "domcontentloaded" });
}

for (const [name, path] of pages) {
  test(`${name} fits its viewport`, async ({ page }) => {
    await page.goto(path, { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
    await expectNoHorizontalOverflow(page);

    if (!process.env.LIVE_SMOKE && !process.env.RESPONSIVE_NO_SNAPSHOTS && visualPages.has(name)) {
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
  await page.locator('input[name="login-username"]').fill(process.env.RESPONSIVE_TEST_USERNAME);
  await page.locator('input[name="login-password"]').fill(process.env.RESPONSIVE_TEST_PASSWORD);
  await page.locator('button[type="submit"]').click();
  await expect(page).not.toHaveURL(/\/accounts\/login\//);
  await page.goto("/wishlist/", { waitUntil: "domcontentloaded" });

  await expectNoHorizontalOverflow(page);
  await expect(page.getByText("Your wishlist is empty.")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("wishlist.png"), fullPage: true });
});

test("design description is available from the T-shirt preview", async ({ page }) => {
  await visitDescribedDesign(page);
  const panel = page.locator("#variant-panel");
  const cardBody = panel.locator(".card-body");
  const trigger = panel.locator("#product-description-information-trigger");
  const content = panel.locator("#product-description-information-content");

  await expect(panel).toBeVisible();
  await expect(trigger).toBeVisible();
  const [cardBodyBox, triggerBox] = await Promise.all([cardBody.boundingBox(), trigger.boundingBox()]);
  expect(cardBodyBox).not.toBeNull();
  expect(triggerBox).not.toBeNull();
  expect(triggerBox.x).toBeGreaterThan(cardBodyBox.x + cardBodyBox.width * 0.7);
  expect(triggerBox.y).toBeGreaterThanOrEqual(cardBodyBox.y);
  expect(triggerBox.y + triggerBox.height).toBeLessThanOrEqual(cardBodyBox.y + cardBodyBox.height);
  await expect(content).toBeHidden();
  await trigger.click();
  await expect(content).toBeVisible();
  await expect(content).toContainText("Jiangchuan cambroernids");
  const [contentBox, viewport] = await Promise.all([content.boundingBox(), page.viewportSize()]);
  expect(contentBox).not.toBeNull();
  expect(contentBox.width).toBeLessThanOrEqual(Math.min(320, viewport.width - 16) + 1);
  expect(contentBox.height).toBeGreaterThanOrEqual(192);
  await page.keyboard.press("Escape");
  await expect(content).toBeHidden();
  await expectNoHorizontalOverflow(page);
});

test("garment information follows the selected style", async ({ page }) => {
  await visitDescribedDesign(page);
  const styleInformationTrigger = page.locator("#style-information-trigger");
  const styleInformation = page.locator("#style-information-content");

  await expect(styleInformationTrigger).toBeVisible();
  await page.getByRole("button", { name: "Women's Tee" }).click();
  await styleInformationTrigger.click();
  await expect(styleInformation).toContainText("AS Colour Women's Maple Tee (AS-4001)");
  await expect(styleInformation).toContainText("3XL");

  await styleInformationTrigger.click();
  await expect(styleInformation).toBeHidden();
  await page.getByRole("button", { name: "Kid's Tee" }).click();
  await styleInformationTrigger.click();
  await expect(styleInformation).toContainText("AS Colour Kids Staple Tee (AS-3005)");
  await expect(styleInformation).not.toContainText("3XL");
  await expectNoHorizontalOverflow(page);
});
