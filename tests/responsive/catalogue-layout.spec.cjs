const { test, expect } = require('@playwright/test');
test.setTimeout(90_000);

test('catalogue pagination has no empty slots, repeats or missing designs', async ({ page }) => {
  await page.goto('/catalogue/');
  await expect(page.locator('.catalogue-product-grid')).toHaveAttribute('data-fit-ready', 'true');
  const seen = new Set();
  const total = Number((await page.locator('.catalogue-results-header').innerText()).match(/\d+/)[0]);
  const visited = new Set();
  while (!visited.has(page.url())) {
    visited.add(page.url());
    const cards = page.locator('.catalogue-product-grid > li');
    const links = await cards.locator('.product-card-title > a').evaluateAll(nodes => nodes.map(a => a.pathname));
    expect(links.length).toBe(await cards.count());
    const size = Number(await page.locator('.catalogue-product-grid').getAttribute('data-page-size'));
    expect(links.length).toBe(Math.min(size, total - seen.size));
    for (const link of links) {
      expect(seen.has(link)).toBe(false);
      seen.add(link);
    }
    if (seen.size === total) break;
    await page.locator('.catalogue-pagination-bottom a[aria-label="Next page"]').click();
    await expect(page.locator('.catalogue-product-grid')).toHaveAttribute('data-fit-ready', 'true');
  }
  expect(seen.size).toBe(total);
});

test('catalogue fits screen height and adapts its page size on resize', async ({ page }) => {
  await page.goto('/catalogue/');
  const grid = page.locator('.catalogue-product-grid');
  await expect(grid).toHaveAttribute('data-fit-ready', 'true');
  for (const [width, height] of [[1440, 900], [1366, 768], [390, 844], [430, 932], [768, 1024], [844, 390]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      height: document.documentElement.scrollHeight,
    })).catch(() => null)).toEqual({ width, height });
    // Wait for resize pagination to settle before inspecting its cards.
    await expect.poll(async () => grid.evaluate(el => {
      const columns = getComputedStyle(el).gridTemplateColumns.split(' ').length;
      return Number(el.dataset.pageSize) % columns;
    }).catch(() => -1)).toBe(0);
    await expect(page.locator('.catalogue-pagination-bottom')).toBeInViewport();
    await expect(page.locator('footer')).toBeInViewport();
  }
});
