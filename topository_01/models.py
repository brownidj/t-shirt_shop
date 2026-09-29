from django.conf import settings
from django.db import models


class DesignRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    idea = models.CharField(max_length=200)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.idea


class MarketingConsent(models.Model):
    """Records an affirmative marketing opt-in separately from the account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketing_consent",
    )
    consented_at = models.DateTimeField(auto_now_add=True)
