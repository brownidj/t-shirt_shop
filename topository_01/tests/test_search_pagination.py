from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from topository_01.search.backends import OffsetWhooshSearchBackend


class CatalogueSearchPaginationTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.backend = OffsetWhooshSearchBackend(
            "default", PATH=self.directory.name, SILENTLY_FAIL=False
        )
        self.backend.setup()
        writer = self.backend.index.writer()
        for position in range(15):
            writer.add_document(
                id=f"catalogue.product.{position + 1}",
                django_ct="catalogue.product",
                django_id=str(position + 1),
                text="underwater fossil design",
                title_exact=f"Design {position:02}",
                category="1",
            )
        for position in range(3):
            writer.add_document(
                id=f"catalogue.product.{100 + position}",
                django_ct="catalogue.product",
                django_id=str(100 + position),
                text="underwater fossil design",
                title_exact=f"Design {position:02} from another category",
                category="4",
            )
        writer.commit()

    def search(self, start, end):
        return self.backend.search(
            "*", sort_by=["title_exact"], start_offset=start, end_offset=end,
            narrow_queries={"category:1"},
        )

    def test_short_final_page_has_no_repeats_or_missing_designs(self):
        first = self.search(0, 9)
        last = self.search(9, 15)
        titles = [result.title_exact for result in first["results"] + last["results"]]

        self.assertEqual(titles, [f"Design {position:02}" for position in range(15)])
        self.assertEqual(len(last["results"]), 6)
        self.assertEqual(last["hits"], 15)

    def test_aligned_and_unaligned_slices_keep_the_requested_order(self):
        for start, end in [(3, 6), (4, 9), (9, 18), (12, None)]:
            with self.subTest(start=start, end=end):
                result = self.search(start, end)
                expected = [f"Design {position:02}" for position in range(15)][start:end]
                self.assertEqual([item.title_exact for item in result["results"]], expected)
                self.assertEqual(result["hits"], 15)

    def test_category_filter_is_retained_on_the_short_final_page(self):
        result = self.backend.search(
            "*", sort_by=["title_exact"], start_offset=9, end_offset=15,
            narrow_queries={"category:1"},
        )
        self.assertEqual([item.pk for item in result["results"]], [str(i) for i in range(10, 16)])
        self.assertEqual(result["hits"], 15)
