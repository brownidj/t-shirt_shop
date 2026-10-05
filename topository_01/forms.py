from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.apps.customer.forms import (
    EmailAuthenticationForm as OscarEmailAuthenticationForm,
    EmailUserCreationForm as OscarEmailUserCreationForm,
)

from .models import DesignRequest, MarketingConsent


class UsernameOrEmailAuthenticationForm(OscarEmailAuthenticationForm):
    """Accept either a username or an email address at sign-in."""

    username = forms.CharField(label=_("Username or email"), max_length=254)


class DesignRequestForm(forms.ModelForm):
    class Meta:
        model = DesignRequest
        fields = ("name", "email", "details")
        widgets = {
            "details": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "details": "Tell us about the design you would like",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            if name == "name":
                field.widget.attrs["placeholder"] = "Your name"
            elif name == "email":
                field.widget.attrs["placeholder"] = "Your email"

    def save(self, commit=True):
        request = super().save(commit=False)
        request.idea = request.details[:200]
        if commit:
            request.save()
        return request


class CustomerRegistrationForm(OscarEmailUserCreationForm):
    """Minimal registration fields, with an optional marketing opt-in."""

    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    marketing_consent = forms.BooleanField(
        label=_("Email me occasional news, new designs and offers"),
        required=False,
    )
    field_order = (
        "email",
        "first_name",
        "last_name",
        "password1",
        "password2",
        "marketing_consent",
        "redirect_url",
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()

        if commit:
            user.save()
            if self.cleaned_data["marketing_consent"]:
                MarketingConsent.objects.update_or_create(user=user)

        return user
