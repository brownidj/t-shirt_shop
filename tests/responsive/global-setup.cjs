const { execFileSync } = require("node:child_process");

const username = `responsive-checker-${process.pid}-${Date.now()}`;
const password = "responsive-test-only";
const responsiveDesignSlug = "responsive-cambroernid";

function manage(command) {
  return execFileSync("python3", ["manage.py", "shell", "-c", command], {
    encoding: "utf8",
    env: process.env,
  });
}

module.exports = async function globalSetup() {
  // Live smoke checks must not create accounts on the production site.
  if (process.env.BASE_URL) {
    return;
  }

  process.env.RESPONSIVE_TEST_USERNAME = username;
  process.env.RESPONSIVE_TEST_PASSWORD = password;
  // GitHub Actions starts with an empty database.  Create the one public
  // design used by product-preview checks, rather than depending on a copy of
  // the live catalogue.  Its image is a committed media asset.
  const designPath = manage(
    "from oscar.apps.catalogue.models import Product, ProductClass, ProductImage; " +
      "product_class, _ = ProductClass.objects.get_or_create(name='Designs'); " +
      "product, _ = Product.objects.get_or_create(slug='responsive-cambroernid', defaults={'title': 'Responsive Cambroernid', 'description': '<p>Jiangchuan cambroernids were U-shaped seafloor animals with stalks and feeding tentacles.</p>', 'product_class': product_class, 'structure': Product.STANDALONE, 'is_public': True}); " +
      "product.title = 'Responsive Cambroernid'; product.description = '<p>Jiangchuan cambroernids were U-shaped seafloor animals with stalks and feeding tentacles.</p>'; product.product_class = product_class; product.structure = Product.STANDALONE; product.is_public = True; product.save(); " +
      "ProductImage.objects.get_or_create(product=product, original='images/products/2026/10/Cambroernid_02_20261012.jpg', defaults={'caption': 'Responsive Cambroernid'}); " +
      "print(product.get_absolute_url())"
  )
    .trim()
    .split("\n")
    .at(-1);
  process.env.RESPONSIVE_DESIGN_PATH = designPath;
  manage(
    "import os; from django.contrib.auth import get_user_model; " +
      "get_user_model().objects.create_user(username=os.environ['RESPONSIVE_TEST_USERNAME'], " +
      "email='responsive-checker@example.invalid', password=os.environ['RESPONSIVE_TEST_PASSWORD'], " +
      "first_name='Responsive')"
  );

  return async () => {
    manage(
      "import os; from django.contrib.auth import get_user_model; " +
        "get_user_model().objects.filter(username=os.environ['RESPONSIVE_TEST_USERNAME']).delete()"
    );
    manage(
      "from oscar.apps.catalogue.models import Product; " +
        "Product.objects.filter(slug='responsive-cambroernid').delete()"
    );
  };
};
