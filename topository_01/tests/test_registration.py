from django.contrib.auth import get_user_model
from django.test import TestCase

from topository_01.forms import CustomerProfileForm, CustomerRegistrationForm


class CustomerRegistrationFormTests(TestCase):
    def form_data(self, **overrides):
        data = {
            "email": "new-shopper@example.test",
            "username": "new-shopper",
            "first_name": "New",
            "last_name": "Shopper",
            "password1": "safe-test-password",
            "password2": "safe-test-password",
        }
        data.update(overrides)
        return data

    def test_duplicate_username_suggests_next_available_username(self):
        get_user_model().objects.create_user(
            username="shopper", email="existing@example.test", password="password"
        )

        form = CustomerRegistrationForm(data=self.form_data(username="shopper"))

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["username"], ["That username is already in use. Try 'shopper1'."]
        )

    def test_registration_saves_the_requested_unique_username(self):
        form = CustomerRegistrationForm(data=self.form_data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.username, "new-shopper")

    def test_profile_requires_a_first_name(self):
        user = get_user_model().objects.create_user(
            username="existing-shopper",
            email="existing@example.test",
            password="password",
        )

        form = CustomerProfileForm(
            user,
            data={"first_name": "", "last_name": "Shopper", "email": user.email},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
