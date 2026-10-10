from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from oscar.apps.catalogue.models import Product
from oscar.test.factories import create_basket

from topository_01.views import (
    add_wishlist_line_to_cart,
    transfer_basket_line_to_wishlist,
    update_wishlist_line_quantity,
)


class BasketWishlistTransferTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="wishlist-shopper",
            email="wishlist-shopper@example.test",
            password="safe-test-password",
        )
        self.basket = create_basket()
        self.line = self.basket.lines.get()

    def configure_line_product(self):
        self.line.product.product_class.name = "T-shirt"
        self.line.product.product_class.save(update_fields=["name"])
        parent = Product.objects.create(
            title="Saved design",
            structure=Product.PARENT,
            product_class=self.line.product.product_class,
        )
        self.line.product.parent = parent
        self.line.product.structure = Product.CHILD
        self.line.product.save(update_fields=["parent", "structure"])

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
        self.configure_line_product()
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        self.client.force_login(self.user)

        response = self.client.get(reverse("wishlist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.line.description)

    def test_default_wishlist_is_named_after_the_shopper(self):
        self.user.first_name = "Ada"
        self.user.save(update_fields=["first_name"])
        wishlist = self.user.wishlists.create()
        self.client.force_login(self.user)

        response = self.client.get(reverse("wishlist"))

        self.assertEqual(response.status_code, 200)
        wishlist.refresh_from_db()
        self.assertEqual(wishlist.name, "Ada")
        self.assertContains(response, "Ada's Wishlist")

    def test_account_wishlist_links_use_the_storefront_wishlist(self):
        wishlist = self.user.wishlists.create()
        self.client.force_login(self.user)

        response = self.client.get(f"/accounts/wishlists/{wishlist.key}/")

        self.assertRedirects(response, reverse("wishlist"), fetch_redirect_response=False)

    def test_wishlist_page_shows_an_unconfigured_design(self):
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        self.client.force_login(self.user)

        response = self.client.get(reverse("wishlist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.line.description)

    def test_add_to_cart_removes_the_saved_item_from_the_wishlist(self):
        self.configure_line_product()
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        wishlist_line = wishlist.lines.get(product=self.line.product)
        self.line.delete()
        self.basket.refresh_from_db()
        self.assertFalse(self.basket.lines.exists())

        request = RequestFactory().post(
            reverse("wishlist_add_to_cart", args=[wishlist_line.pk])
        )
        request.user = self.user
        request.basket = self.basket
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)

        response = add_wishlist_line_to_cart(request, wishlist_line.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("wishlist"))
        self.assertFalse(wishlist.lines.filter(pk=wishlist_line.pk).exists())
        self.assertEqual(
            self.basket.lines.get(product=self.line.product).quantity,
            wishlist_line.quantity,
        )

    def test_zero_quantity_removes_the_shoppers_saved_item(self):
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        wishlist_line = wishlist.lines.get(product=self.line.product)
        request = RequestFactory().post(
            reverse("wishlist_update_quantity", args=[wishlist_line.pk]), {"quantity": 0}
        )
        request.user = self.user
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)

        response = update_wishlist_line_quantity(request, wishlist_line.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("wishlist"))
        self.assertFalse(wishlist.lines.filter(pk=wishlist_line.pk).exists())

    def test_quantity_update_changes_the_saved_quantity(self):
        wishlist = self.user.wishlists.create()
        wishlist.add(self.line.product)
        wishlist_line = wishlist.lines.get(product=self.line.product)
        request = RequestFactory().post(
            reverse("wishlist_update_quantity", args=[wishlist_line.pk]), {"quantity": 3}
        )
        request.user = self.user
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)

        response = update_wishlist_line_quantity(request, wishlist_line.pk)

        self.assertEqual(response.status_code, 302)
        wishlist_line.refresh_from_db()
        self.assertEqual(wishlist_line.quantity, 3)
