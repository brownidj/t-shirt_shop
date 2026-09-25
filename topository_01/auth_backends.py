from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate a shopper with either their username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get(get_user_model().USERNAME_FIELD)
        if not identifier or password is None:
            return None

        user = super().authenticate(request, username=identifier, password=password)
        if user is not None:
            return user

        user_model = get_user_model()
        try:
            user = user_model._default_manager.get(email__iexact=identifier)
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
