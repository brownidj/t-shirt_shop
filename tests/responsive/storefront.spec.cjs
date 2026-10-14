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
  const path = process.env.RESPONSIVE_DESIGN_PATH;
  if (!path || !path.startsWith("/catalogue/responsive-cambroernid_")) {
    throw new Error("Responsive test design was not created by global setup");
  }
  await page.goto(path, { waitUntil: "domcontentloaded" });
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

test("legal footer links stay on one separated row on every viewport", async ({ page }) => {
  await page.goto("/accounts/login/", { waitUntil: "domcontentloaded" });
  const links = page.locator('nav[aria-label="Legal information"] a');
  await expect(links).toHaveCount(3);

  const boxes = await links.evaluateAll((elements) =>
    elements.map((element) => {
      const box = element.getBoundingClientRect();
      return { left: box.left, right: box.right, top: box.top, bottom: box.bottom };
    })
  );
  for (let index = 1; index < boxes.length; index += 1) {
    const previous = boxes[index - 1];
    const current = boxes[index];
    const hasHorizontalGap = current.left >= previous.right + 8;
    expect(Math.abs(current.top - previous.top)).toBeLessThanOrEqual(1);
    expect(hasHorizontalGap).toBeTruthy();
  }
  await expectNoHorizontalOverflow(page);
});

test("design description is available from the T-shirt preview", async ({ page }) => {
  await visitDescribedDesign(page);
  const panel = page.locator("#variant-panel");
  const preview = panel.locator(".variant-panel-preview");
  const previewImage = panel.locator("#variant-panel-image");
  const trigger = panel.locator("#product-description-information-trigger");
  const content = panel.locator("#product-description-information-content");

  await expect(panel).toBeVisible();
  await expect.poll(async () => previewImage.evaluate((image) => image.getBoundingClientRect().width)).toBeGreaterThan(100);
  await expect(trigger).toBeVisible();
  const [previewBox, triggerBox] = await Promise.all([preview.boundingBox(), trigger.boundingBox()]);
  expect(previewBox).not.toBeNull();
  expect(triggerBox).not.toBeNull();
  expect(triggerBox.x).toBeGreaterThan(previewBox.x + previewBox.width * 0.7);
  expect(triggerBox.y).toBeGreaterThanOrEqual(previewBox.y);
  expect(triggerBox.y + triggerBox.height).toBeLessThanOrEqual(previewBox.y + previewBox.height);
  await expect(content).toBeHidden();
  await trigger.click();
  await expect(content).toBeVisible();
  await expect(content).toContainText("Jiangchuan cambroernids");
  const [contentBox, viewport] = await Promise.all([content.boundingBox(), page.viewportSize()]);
  expect(contentBox).not.toBeNull();
  expect(contentBox.width).toBeLessThanOrEqual(Math.min(288, viewport.width - 16) + 1);
  expect(contentBox.height).toBeGreaterThanOrEqual(192);
  await expect.poll(async () => {
    const box = await content.boundingBox();
    return box && box.x >= 0 && box.x + box.width <= viewport.width + 1;
  }).toBeTruthy();
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
