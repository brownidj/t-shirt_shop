# Responsive and accessibility browser checks

The responsive suite checks the shop at nine representative viewport sizes:

| Name | Viewport |
| --- | --- |
| Small phone | 390 x 844 |
| Large phone | 430 x 932 |
| iPhone 16 Pro | 402 x 874 |
| OPPO A96 (CPH2333) | 360 x 804 |
| Tablet | 768 x 1024 |
| iPad mini (A17 Pro) | 744 x 1133 |
| Laptop | 1366 x 768 |
| MacBook Pro 16-inch (2019) | 1536 x 960 |
| Desktop | 1440 x 900 |

It also runs the small-phone checks in WebKit, the browser engine used by Safari.

## One-time setup

```sh
npm install
npx playwright install
```

## Normal local check

```sh
npm run test:responsive
```

This starts a local Django server automatically and checks the home page, catalogue, login, design-request, basket, and signed-in empty wishlist pages. Playwright itself creates a one-use test shopper for local runs, then removes it after the run, so this also works when Playwright is run directly. It verifies that none overflow horizontally and compares stable pages with approved screenshots. The first run creates the screenshots; approve intentional design changes with:

```sh
npm run test:responsive:update
```

## Automatic GitHub check

Every push and pull request runs the same public and signed-in checks, including axe accessibility scans, on a temporary copy of the site. The automated run checks all ten viewport/browser profiles for horizontal overflow, but does not compare screenshots: browser font rendering can differ between the hosted runner and a developer's Mac. Screenshot comparisons remain part of the local pre-release check above.

## Read-only live smoke check

After deployment, run:

```sh
npm run test:responsive:live
```

This makes only GET requests to the live site and checks each public page for horizontal overflow. It does not compare screenshots or submit forms, so it cannot create an order or charge a card.

## Automated accessibility checks

The suite uses `@axe-core/playwright` to check automatically detectable WCAG 2.0,
2.1 and 2.2 Level A/AA rules across all ten browser/viewport profiles. Run it alone:

```sh
npm run test:accessibility
# For a quick desktop-only check:
npm run test:accessibility -- --project=desktop
```

Scans cover the homepage, catalogue, login, registration, password-reset form,
design-request form, empty cart, populated cart and signed-in empty wishlist.
The product page is checked normally and with the description and garment/size
information panels open. Invalid login and empty design-request submissions also
receive scans. These tests do not submit payments, send reset emails or send a
valid design request. They skip external servers (`BASE_URL`), preserving the
read-only live smoke command.

Each scan attaches the complete axe JSON and a readable Markdown summary to the
Playwright HTML report, including findings that need manual review. Any detected
violation fails the test; no rules or page regions are excluded. Inconclusive
checks remain visible for review rather than being treated as passes.

```sh
npx playwright show-report
```

GitHub Actions uploads `browser-test-reports` (HTML, findings, failure screenshots
and traces) even when a check fails, keeping it for 14 days. This workflow runs
when the changes are pushed; local checks do not trigger a hosted run.

Browser runs use an isolated Whoosh index in `tmp/responsive-search-index`, rebuilt
with the fixture design, so fresh CI databases actually display a product and the
normal catalogue index is preserved. `TOPOSITORY_SEARCH_INDEX_PATH` can override
that location. A second disposable shopper owns the fixture cart; both shoppers
and the test design are removed at teardown.

For an isolated local database, migrate it first and use the same environment for
the test run (with your Python virtual environment activated):

```sh
export TOPOSITORY_DB_PATH="$PWD/tmp/browser-checks.sqlite3"
mkdir -p tmp
python manage.py migrate --noinput
npm run test:accessibility
```

Automated scans cover only the rendered states exercised here. Continue the
shopper book's keyboard, screen-reader and usability checks; passing axe does not
establish complete WCAG compliance. The password-reset scan checks the form, not
email delivery or completion of a reset.
