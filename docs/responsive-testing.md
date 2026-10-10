# Responsive browser checks

The responsive suite checks the shop at five representative viewport sizes:

| Name | Viewport |
| --- | --- |
| Small phone | 390 x 844 |
| Large phone | 430 x 932 |
| Tablet | 768 x 1024 |
| Laptop | 1366 x 768 |
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

This starts a local Django server automatically and checks the home page, catalogue, login, design-request, and basket pages. It verifies that none overflow horizontally and compares them with approved screenshots. The first run creates the screenshots; approve intentional design changes with:

```sh
npm run test:responsive:update
```

## Signed-in wishlist inspection

Use a dedicated test account, never a customer account:

```sh
RESPONSIVE_TEST_USERNAME=responsive-test \
RESPONSIVE_TEST_PASSWORD='password' \
npm run test:responsive
```

This opens the wishlist, checks the visible quantity controls, verifies no horizontal overflow, and saves an inspection screenshot. It does not alter the wishlist or start checkout.

## Read-only live smoke check

After deployment, run:

```sh
npm run test:responsive:live
```

This makes only GET requests to the live site and checks each public page for horizontal overflow. It does not compare screenshots or submit forms, so it cannot create an order or charge a card.
