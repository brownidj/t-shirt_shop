# Responsive browser checks

The responsive suite checks the shop at five representative viewport sizes:

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

Every push and pull request runs the same public and signed-in checks on a temporary copy of the site. The automated run checks all ten viewport/browser profiles for horizontal overflow, but does not compare screenshots: browser font rendering can differ between the hosted runner and a developer's Mac. Screenshot comparisons remain part of the local pre-release check above.

## Read-only live smoke check

After deployment, run:

```sh
npm run test:responsive:live
```

This makes only GET requests to the live site and checks each public page for horizontal overflow. It does not compare screenshots or submit forms, so it cannot create an order or charge a card.
