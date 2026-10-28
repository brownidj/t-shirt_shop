const { test, expect } = require('@playwright/test');

test('catalogue pagination has no empty slots, repeats or missing designs', async ({ page }) => {
  await page.goto('/catalogue/');
  const seen = new Set();
  const total = Number((await page.locator('.catalogue-results-header').innerText()).match(/\d+/)[0]);
  const visited = new Set();
  while (!visited.has(page.url())) {
    visited.add(page.url());
    const cards = page.locator('.catalogue-product-grid > li');
    const links = await cards.locator('.product-card-title > a').evaluateAll(nodes => nodes.map(a => a.pathname));
    expect(links.length).toBe(await cards.count());
    expect(links.length).toBe(Math.min(12, total - seen.size));
    for (const link of links) {
      expect(seen.has(link)).toBe(false);
      seen.add(link);
    }
    if (seen.size === total) break;
    await page.locator('.catalogue-pagination-bottom a[aria-label="Next page"]').click();
  }
  expect(seen.size).toBe(total);
});

test('catalogue columns use available width and adapt without losing designs', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/catalogue/');
  const grid = page.locator('.catalogue-product-grid');
  const titles = await grid.locator('.product-card-title > a').allTextContents();
  const columns = () => grid.evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
  expect(await columns()).toBeGreaterThanOrEqual(3);
  const sidebar = await page.locator('.sidebar').boundingBox();
  expect(sidebar.width).toBeLessThanOrEqual(220);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await columns()).toBe(1);
  expect(await grid.locator('.product-card-title > a').allTextContents()).toEqual(titles);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.setViewportSize({ width: 768, height: 1024 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(768);
});
