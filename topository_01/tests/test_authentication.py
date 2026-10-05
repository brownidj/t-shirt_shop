from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from topository_01.forms import UsernameOrEmailAuthenticationForm


class UsernameOrEmailLoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="shopper-name",
            email="shopper@example.test",
            password="safe-test-password",
        )

    def login(self, identifier):
        return self.client.post(
            reverse("customer:login"),
            {
                "login-username": identifier,
                "login-password": "safe-test-password",
                "login-redirect_url": "",
                "login_submit": "Login",
            },
        )

    def test_login_with_username(self):
        response = self.login(self.user.username)

        self.assertRedirects(
            response, reverse("customer:summary"), fetch_redirect_response=False
        )
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_login_with_email(self):
        response = self.login(self.user.email)

        self.assertRedirects(
            response, reverse("customer:summary"), fetch_redirect_response=False
        )
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_login_identifier_label_mentions_email_and_username(self):
        form = UsernameOrEmailAuthenticationForm(host="tshirts.topository.org")

        self.assertEqual(form.fields["username"].label, "Email or username")
