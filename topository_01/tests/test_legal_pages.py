from django.test import TestCase


class LegalFlatPageTests(TestCase):
    def test_each_public_legal_page_is_available(self):
        pages = {
            "/terms-of-sale/": b"Terms of Sale",
            "/returns-refunds-cancellations/": b"Australian Consumer Law",
            "/privacy-policy/": b"Privacy Policy",
        }

        for url, expected_content in pages.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_content.decode())

    def test_legal_pages_include_the_shared_footer_links(self):
        response = self.client.get("/terms-of-sale/")

        self.assertContains(response, 'href="/returns-refunds-cancellations/"')
        self.assertContains(response, 'href="/privacy-policy/"')

    def test_returns_page_uses_the_short_title_in_its_breadcrumb(self):
        response = self.client.get("/returns-refunds-cancellations/")

        self.assertContains(response, "Returns &amp; Refunds")
        self.assertNotContains(response, "Returns, Refunds and Cancellations Policy")
