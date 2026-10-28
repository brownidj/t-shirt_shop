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

test('desktop fits screen height while mobile keeps scrolling pages', async ({ page }) => {
  await page.goto('/catalogue/');
  const grid = page.locator('.catalogue-product-grid');
  await expect(grid).toHaveAttribute('data-fit-ready', 'true');
  for (const [width, height] of [[1440, 900], [1366, 768], [390, 844], [430, 932], [768, 1024], [844, 390]]) {
    await page.setViewportSize({ width, height });
    const mobile = await page.evaluate(() => matchMedia('(max-width: 1023px), (pointer: coarse)').matches);
    await expect(grid).toHaveAttribute('data-layout-mode', mobile ? 'scroll' : 'fit');
    if (mobile) {
      await expect(grid).toHaveAttribute('data-page-size', '12');
      await expect(page.locator('body')).not.toHaveClass(/catalogue-fit-ready/);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth).catch(() => null)).toBe(width);
      const count = await grid.locator('.product_pod').count();
      if (count > 3) {
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollHeight).catch(() => 0)).toBeGreaterThan(height);
      }
      await page.locator('.catalogue-pagination-bottom').scrollIntoViewIfNeeded();
      await expect(page.locator('.catalogue-pagination-bottom')).toBeInViewport();
      await page.evaluate(() => scrollTo(0, 0));
    } else {
      await expect.poll(() => page.evaluate(() => ({
        width: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
      })).catch(() => null)).toEqual({ width, height });
      await expect(page.locator('.catalogue-pagination-bottom')).toBeInViewport();
      await expect(page.locator('footer')).toBeInViewport();
    }
  }
});
