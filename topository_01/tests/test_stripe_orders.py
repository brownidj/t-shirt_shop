from types import SimpleNamespace

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from oscar.core.loading import get_model
from oscar.test.factories import create_basket

from topository_01.views import (
    _create_order_from_stripe_session,
    _stripe_customer_for_user,
    stripe_checkout,
)


Country = get_model("address", "Country")


class StripeOrderCreationTests(TestCase):
    def setUp(self):
        Country.objects.create(iso_3166_1_a2="AU", printable_name="Australia")

    def session_for(self, basket, user=None):
        return SimpleNamespace(
            id=f"cs_test_{basket.id}",
            payment_status="paid",
            currency="aud",
            amount_total=6490,
            shipping_cost=SimpleNamespace(amount_total=1000),
            metadata={
                "basket_id": str(basket.id),
                "user_id": str(user.id) if user else "",
            },
            customer_details=SimpleNamespace(
                name="Ada Lovelace", email="ada@example.test", phone="0400 000 000"
            ),
            shipping_details=SimpleNamespace(
                name="Ada Lovelace",
                address=SimpleNamespace(
                    line1="1 Example Street",
                    line2="Unit 2",
                    city="Townsville",
                    state="Queensland",
                    postal_code="4810",
                    country="AU",
                ),
            ),
        )

    def test_paid_guest_session_creates_an_order_with_delivery_details(self):
        basket = create_basket()

        order = _create_order_from_stripe_session(self.session_for(basket))

        self.assertIsNone(order.user)
        self.assertEqual(order.guest_email, "ada@example.test")
        self.assertEqual(order.shipping_address.line1, "1 Example Street")
        self.assertEqual(order.shipping_address.line3, "Townsville")
        self.assertEqual(order.shipping_incl_tax, 10)
        basket.refresh_from_db()
        self.assertEqual(basket.status, basket.SUBMITTED)

    def test_paid_session_with_optional_address_fields_missing_creates_an_order(self):
        basket = create_basket()
        session = self.session_for(basket)
        session.shipping_details.address.line2 = None
        session.shipping_details.address.state = None
        session.customer_details.phone = None

        order = _create_order_from_stripe_session(session)

        self.assertEqual(order.shipping_address.line2, "")
        self.assertEqual(order.shipping_address.state, "")
        self.assertEqual(order.shipping_address.phone_number, "")

    def test_paid_account_session_appears_in_that_shoppers_order_history(self):
        basket = create_basket()
        user = get_user_model().objects.create_user(
            username="shopper",
            email="shopper@example.test",
            password="safe-test-password",
        )

        order = _create_order_from_stripe_session(self.session_for(basket, user))

        self.assertEqual(order.user, user)
        self.assertTrue(user.orders.filter(pk=order.pk).exists())
        self.assertEqual(user.addresses.count(), 1)

    def test_replayed_stripe_event_does_not_duplicate_an_order(self):
        basket = create_basket()
        session = self.session_for(basket)

        first_order = _create_order_from_stripe_session(session)
        second_order = _create_order_from_stripe_session(session)

        self.assertEqual(first_order.pk, second_order.pk)


class StripeCustomerTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            iso_3166_1_a2="AU", printable_name="Australia"
        )
        self.user = get_user_model().objects.create_user(
            username="shopper", email="shopper@example.test", password="safe-test-password"
        )
        self.address = self.user.addresses.create(
            first_name="Ada",
            last_name="Lovelace",
            line1="1 Example Street",
            line3="Townsville",
            state="Queensland",
            postcode="4810",
            country=self.country,
            phone_number="0400 000 000",
            is_default_for_shipping=True,
        )

    def test_saved_delivery_address_creates_a_stripe_customer(self):
        customer_api = SimpleNamespace(
            list=lambda **kwargs: SimpleNamespace(data=[]),
            create=lambda **kwargs: SimpleNamespace(id="cus_topository"),
        )
        stripe = SimpleNamespace(Customer=customer_api)

        customer_id = _stripe_customer_for_user(stripe, self.user)

        self.assertEqual(customer_id, "cus_topository")

    def test_existing_customer_is_updated_from_saved_delivery_address(self):
        customer = SimpleNamespace(
            id="cus_existing", metadata={"topository_user_id": str(self.user.id)}
        )
        updates = []
        customer_api = SimpleNamespace(
            list=lambda **kwargs: SimpleNamespace(data=[customer]),
            modify=lambda customer_id, **kwargs: updates.append((customer_id, kwargs)),
        )
        stripe = SimpleNamespace(Customer=customer_api)

        customer_id = _stripe_customer_for_user(stripe, self.user)

        self.assertEqual(customer_id, "cus_existing")
        self.assertEqual(updates[0][1]["shipping"]["address"]["line1"], "1 Example Street")


class StripeCheckoutPolicyTests(TestCase):
    def test_checkout_without_policy_acceptance_returns_to_basket(self):
        request = RequestFactory().post(reverse("stripe_checkout"))
        SessionMiddleware(lambda request: None).process_request(request)
        request.session.save()
        request.basket = create_basket()
        request._messages = FallbackStorage(request)

        response = stripe_checkout(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("basket:summary"))


class FulfilmentDashboardTests(TestCase):
    def setUp(self):
        Country.objects.create(iso_3166_1_a2="AU", printable_name="Australia")
        self.order = _create_order_from_stripe_session(
            StripeOrderCreationTests.session_for(self, create_basket())
        )
        self.staff = get_user_model().objects.create_superuser(
            username="staff", email="staff@example.test", password="safe-test-password"
        )

    def test_fulfilment_draft_is_staff_only_and_never_shopper_facing(self):
        url = reverse("fulfilment_order", kwargs={"number": self.order.number})

        anonymous_response = self.client.get(url)
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Garment Printing Group")
        self.assertContains(response, "No Garment Printing Group recipient has been configured")

    def test_order_detail_links_to_the_fulfilment_request(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("dashboard:order-detail", kwargs={"number": self.order.number})
        )

        self.assertContains(response, "Fulfilment request")
        self.assertContains(
            response,
            reverse("fulfilment_order", kwargs={"number": self.order.number}),
        )
