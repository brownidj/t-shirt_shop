const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

// Stateful scans use only the disposable local shopper created by global setup.
// Keep the existing live smoke command read-only, including when credentials exist.
test.skip(Boolean(process.env.BASE_URL), "Accessibility journeys run against the local test shop only.");
test.setTimeout(60_000);

async function visit(page, path) {
  const response = await page.goto(path, { waitUntil: "domcontentloaded" });
  expect(response.ok(), `Page ${path} must load before scanning`).toBeTruthy();
}

async function scan(page, testInfo, state) {
  await expect(page.locator("main#main-content")).toBeVisible();
  await expect(page.getByRole("link", { name: "Skip to main content", exact: true })).toHaveAttribute("href", "#main-content");
  await page.evaluate(() => document.fonts.ready);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  await testInfo.attach(`${state}-axe.json`, {
    body: JSON.stringify(results, null, 2),
    contentType: "application/json",
  });
  const sections = [
    `# Accessibility: ${state}`,
    `URL: ${page.url()}`,
    `Browser profile: ${testInfo.project.name}`,
    `Violations: ${results.violations.length}; checks needing review: ${results.incomplete.length}`,
    "Automated WCAG A/AA checks do not establish full accessibility compliance.",
  ];
  for (const [label, findings] of [["Violations", results.violations], ["Needs manual review", results.incomplete]]) {
    sections.push(`\n## ${label}`);
    if (!findings.length) sections.push("None detected.");
    for (const finding of findings) {
      sections.push(`\n### ${finding.id} (${finding.impact || "unrated"}): ${finding.help}`, finding.helpUrl);
      for (const node of finding.nodes) {
        sections.push(`- Element: ${node.target.join(" / ")}`, `  ${node.failureSummary || node.html}`);
      }
    }
  }
  await testInfo.attach(`${state}-findings.md`, { body: sections.join("\n"), contentType: "text/markdown" });
  const failures = results.violations.map(({ id, impact, nodes }) => ({ id, impact, targets: nodes.map(node => node.target) }));
  expect(failures, `Accessibility violations in ${state}; see attached findings and axe JSON`).toEqual([]);
}

for (const [name, path] of [
  ["home", "/"], ["catalogue", "/catalogue/"], ["login", "/accounts/login/"],
  ["registration", "/accounts/register/"], ["password-reset", "/password-reset/"],
  ["design-request", "/request-a-design/"], ["empty-cart", "/basket/"],
]) {
  test(`${name} has no axe accessibility violations @accessibility`, async ({ page }, testInfo) => {
    await visit(page, path);
    if (name === "catalogue") {
      await expect(page.getByRole("link", { name: "Responsive Cambroernid", exact: true }).first()).toBeVisible();
    }
    await scan(page, testInfo, name);
  });
}

async function visitProduct(page) {
  const path = process.env.RESPONSIVE_DESIGN_PATH;
  if (!path || !path.startsWith("/catalogue/responsive-cambroernid_")) {
    throw new Error("Global setup must create the disposable test design");
  }
  await visit(page, path);
  await expect(page.locator("#variant-panel")).toBeVisible();
}

for (const [name, trigger, content] of [
  ["product", null, null],
  ["product-description-open", "#product-description-information-trigger", "#product-description-information-content"],
  ["garment-information-open", "#style-information-trigger", "#style-information-content"],
]) {
  test(`${name} has no axe accessibility violations @accessibility`, async ({ page }, testInfo) => {
    await visitProduct(page);
    if (trigger) {
      await page.locator(trigger).click();
      await expect(page.locator(content)).toBeVisible();
    }
    await scan(page, testInfo, name);
  });
}

test("login validation has no axe accessibility violations @accessibility", async ({ page }, testInfo) => {
  await visit(page, "/accounts/login/");
  await page.locator('[name="login-username"]').fill(process.env.RESPONSIVE_TEST_USERNAME);
  await page.locator('[name="login-password"]').fill("deliberately-incorrect-test-password");
  await page.locator('button[name="login_submit"]').click();
  await expect(page.locator("#login_form .alert-danger").first()).toBeVisible();
  await scan(page, testInfo, "login-validation");
});

test("design-request validation has no axe accessibility violations @accessibility", async ({ page }, testInfo) => {
  await visit(page, "/request-a-design/");
  // This form opts out of browser validation; an empty POST cannot send a request email.
  await page.getByRole("button", { name: "Send request" }).click();
  await expect(page.locator("form .text-danger").first()).toBeVisible();
  await scan(page, testInfo, "design-request-validation");
});

test("signed-in wishlist has no axe accessibility violations @accessibility", async ({ page }, testInfo) => {
  await visit(page, "/accounts/login/");
  await page.locator('[name="login-username"]').fill(process.env.RESPONSIVE_TEST_USERNAME);
  await page.locator('[name="login-password"]').fill(process.env.RESPONSIVE_TEST_PASSWORD);
  await page.locator('button[name="login_submit"]').click();
  await expect(page).not.toHaveURL(/\/accounts\/login\//);
  await visit(page, "/wishlist/");
  await expect(page.getByText("Your wishlist is empty.")).toBeVisible();
  await scan(page, testInfo, "signed-in-wishlist");
});


test("populated cart has no axe accessibility violations @accessibility", async ({ page }, testInfo) => {
  await visit(page, "/accounts/login/");
  await page.locator('[name="login-username"]').fill(process.env.RESPONSIVE_CART_USERNAME);
  await page.locator('[name="login-password"]').fill(process.env.RESPONSIVE_TEST_PASSWORD);
  await page.locator('button[name="login_submit"]').click();
  await expect(page).not.toHaveURL(/\/accounts\/login\//);
  await visit(page, "/basket/");
  await expect(page.locator("#basket_formset .basket-items")).toHaveCount(1);
  await scan(page, testInfo, "populated-cart");
});
