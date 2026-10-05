from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from oscar.test.factories import create_basket

from topository_01.views import transfer_basket_line_to_wishlist


class BasketWishlistTransferTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="wishlist-shopper",
            email="wishlist-shopper@example.test",
            password="safe-test-password",
        )
        self.basket = create_basket()
        self.line = self.basket.lines.get()

    def test_transfer_saves_the_exact_basket_line_and_removes_it(self):
        request = RequestFactory().post(
            reverse("basket_transfer_to_wishlist"), {"line_id": self.line.pk}
        )
        request.user = self.user
        request.basket = self.basket
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)

        response = transfer_basket_line_to_wishlist(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("basket:summary"))
        self.assertFalse(self.basket.lines.filter(pk=self.line.pk).exists())
        wishlist_line = self.user.wishlists.get().lines.get()
        self.assertEqual(wishlist_line.product_id, self.line.product_id)
        self.assertEqual(wishlist_line.quantity, self.line.quantity)

    def test_wishlist_page_shows_the_shoppers_saved_items(self):
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        self.client.force_login(self.user)

        response = self.client.get(reverse("wishlist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.line.description)
