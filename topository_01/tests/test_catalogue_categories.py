from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from haystack import connections
from oscar.core.loading import get_model
from PIL import Image
from sorl.thumbnail import get_thumbnail


Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")


class CatalogueCategoryIntegrationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        search_settings = {
            "default": {
                **settings.HAYSTACK_CONNECTIONS["default"],
                "PATH": root / "search",
            }
        }
        # Use the configured engine and real product index, but keep test
        # images and realtime indexing away from the working catalogue.
        settings_override = self.settings(
            HAYSTACK_CONNECTIONS=search_settings,
            MEDIA_ROOT=root / "media",
            OSCAR_MISSING_IMAGE_URL="placeholder.jpg",
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    "LOCATION": self.directory.name,
                }
            },
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        connection_info = patch.object(connections, "connections_info", search_settings)
        connection_info.start()
        self.addCleanup(connection_info.stop)
        cached_connections = patch.object(
            connections.thread_local, "connections", {}, create=True
        )
        cached_connections.start()
        self.addCleanup(cached_connections.stop)

        self.paleo = Category.add_root(name="Paleontology", slug="paleo")
        self.scuba = Category.add_root(name="Scuba", slug="scuba")
        self.design_class = ProductClass.objects.create(name="Designs")
        self.paleo_only = [
            self.create_design(f"Fossil {position:02}", self.paleo)
            for position in range(settings.OSCAR_PRODUCTS_PER_PAGE + 5)
        ]
        self.scuba_only = self.create_design("Reef Dive", self.scuba)
        self.tully = self.create_design("Tully Monster", self.paleo, self.scuba)
        artwork = BytesIO()
        Image.new("RGB", (30, 20), (0, 80, 110)).save(artwork, format="JPEG")
        Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
        (Path(settings.MEDIA_ROOT) / "placeholder.jpg").write_bytes(artwork.getvalue())
        self.image = ProductImage.objects.create(
            product=self.tully,
            original=SimpleUploadedFile(
                "tully-monster.jpg", artwork.getvalue(), content_type="image/jpeg",
            ),
            caption="Tully Monster",
        )
        backend = connections["default"].get_backend()
        index = connections["default"].get_unified_index().get_index(Product)
        # Category memberships are added after save, so rebuild from the
        # database exactly as catalogue publication does.
        backend.update(index, Product.objects.all())

    def create_design(self, title, *categories):
        product = Product.objects.create(
            title=title,
            product_class=self.design_class,
            structure=Product.STANDALONE,
            is_public=True,
        )
        product.categories.add(*categories)
        return product

    def test_shared_design_and_artwork_appear_in_both_category_pages(self):
        first_page = self.client.get(self.paleo.get_absolute_url())
        last_page = self.client.get(self.paleo.get_absolute_url(), {"page": 2})
        scuba_page = self.client.get(self.scuba.get_absolute_url())
        for response in [first_page, last_page, scuba_page]:
            self.assertEqual(response.status_code, 200)

        paleo_ids = [
            result.object.pk
            for response in [first_page, last_page]
            for result in response.context["page_obj"]
        ]
        self.assertEqual(paleo_ids, [p.pk for p in self.paleo_only] + [self.tully.pk])
        self.assertEqual(last_page.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(len(last_page.context["page_obj"]), 6)
        self.assertEqual(
            [result.object.pk for result in scuba_page.context["page_obj"]],
            [self.scuba_only.pk, self.tully.pk],
        )

        thumbnail = get_thumbnail(self.image.original, "x155", upscale=False)
        self.assertTrue(thumbnail.storage.exists(thumbnail.name))
        for response in [last_page, scuba_page]:
            self.assertContains(response, self.tully.get_absolute_url())
            self.assertContains(response, thumbnail.url)

    def test_shared_designs_appear_in_both_slideshow_sections(self):
        shared_designs = [self.tully]
        for title in ["Burgess Shale", "Dunkleosteus", "Yunnanzoon"]:
            product = self.create_design(title, self.paleo, self.scuba)
            shared_designs.append(product)
            ProductImage.objects.create(product=product, original=self.image.original.name)
        for product in [self.paleo_only[0], self.scuba_only]:
            ProductImage.objects.create(product=product, original=self.image.original.name)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        slides = response.context["slides"]
        for product in shared_designs:
            with self.subTest(design=product.title):
                matching = [s for s in slides if s["product_url"] == product.get_absolute_url()]
                self.assertEqual([s["category"] for s in matching], ["Paleontology", "Scuba"])
                self.assertEqual(matching[0]["url"], matching[1]["url"])
                self.assertTrue(matching[0]["url"].startswith(self.image.original.url + "?v="))

        expected = [
            (category, title)
            for category, titles in [
                ("Paleontology", [p.title for p in shared_designs] + [self.paleo_only[0].title]),
                ("Scuba", [p.title for p in shared_designs] + [self.scuba_only.title]),
            ]
            for title in sorted(titles, key=str.casefold)
        ]
        self.assertEqual([(s["category"], s["alt"]) for s in slides], expected)

    def test_slideshow_keeps_artwork_without_a_category(self):
        product = self.create_design("Uncategorised artwork")
        ProductImage.objects.create(product=product, original=self.image.original.name)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        matching = [
            s for s in response.context["slides"]
            if s["product_url"] == product.get_absolute_url()
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["category"], "Other designs")
