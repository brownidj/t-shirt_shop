# Storefront test procedure

Use this procedure before releasing a change to the shop's layout or shopper-facing features.

## One-time setup

From the project folder, install the JavaScript test tools and their browsers:

```sh
npm install
npx playwright install
```

## Full local test

Run this before committing a change:

```sh
npm run test:responsive
```

This starts the local shop automatically and checks the home page, catalogue, login, design request, basket, and a signed-in wishlist in every configured format.

Expected result:

```text
60 passed
```

There should be no skipped tests. The test creates a unique temporary shopper for the wishlist check and removes it automatically when the run finishes, including after a failure or interruption.

You can also run the same full check directly:

```sh
npx playwright test
```

## Visual layout comparison

The full local test compares stable pages with approved screenshots. If you have intentionally changed the appearance, review the differences and then update the approved screenshots with:

```sh
npm run test:responsive:update
```

Do not update screenshots merely to make an unexpected layout problem pass.

## Read-only live check

After deploying, check the public website with:

```sh
npm run test:responsive:live
```

Expected result:

```text
50 passed
10 skipped
```

The ten skipped tests are the signed-in wishlist checks. This is deliberate: the live check does not create accounts, sign in, submit forms, or change the production website. It only checks public pages for horizontal overflow.

## If a test fails

1. Read the failing test name and open the HTML report shown at the end of the run:

   ```sh
   npx playwright show-report
   ```

2. Reproduce the issue in the named screen format using the browser's responsive device view.
3. Fix the layout or feature issue.
4. Run the full local test again. Do not treat the check as complete until it reports `60 passed`.
5. After deployment, run the read-only live check and confirm `50 passed` and `10 skipped`.

## Screen formats covered

The suite covers small and large phones, iPhone 16 Pro, OPPO A96 (CPH2333), tablet, iPad mini (A17 Pro), laptop, MacBook Pro 16-inch (2019), desktop, and a Safari-style phone browser. See [responsive-testing.md](responsive-testing.md) for their viewport sizes and technical details.
