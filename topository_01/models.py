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


class FulfilmentSupplier(models.Model):
    """A POD supplier eligible to receive private fulfilment requests."""

    name = models.CharField(max_length=200, unique=True)
    supports_blind_shipping = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    proof_required = models.BooleanField(default=True)
    address = models.TextField(blank=True)
    sales_email = models.EmailField(blank=True)
    support_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class FulfilmentContact(models.Model):
    """A named account manager at a POD fulfilment supplier."""

    supplier = models.ForeignKey(
        FulfilmentSupplier, on_delete=models.CASCADE, related_name="contacts"
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("supplier", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("supplier", "email"), name="unique_fulfilment_contact_email"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.supplier})"


DEFAULT_FULFILMENT_INSTRUCTIONS = """Please send a finished T-shirt design preview to Topository for approval before production.

Send the finished product by normal delivery directly to the shopper's address below.

Send the invoice to Topository at info@tshirts.topository.org only. Do not include supplier pricing, invoice details, or supplier correspondence in any shopper communication or delivery."""


class FulfilmentRequest(models.Model):
    """The private production hand-off for one paid shop order."""

    STATUS_AWAITING_REVIEW = "awaiting_review"
    STATUS_REQUEST_SENT = "request_sent"
    STATUS_PROOF_RECEIVED = "proof_received"
    STATUS_APPROVED = "approved"
    STATUS_IN_PRODUCTION = "in_production"
    STATUS_SHIPPED = "shipped"
    STATUS_CHOICES = (
        (STATUS_AWAITING_REVIEW, "Awaiting review"),
        (STATUS_REQUEST_SENT, "Request sent"),
        (STATUS_PROOF_RECEIVED, "Proof received"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_IN_PRODUCTION, "In production"),
        (STATUS_SHIPPED, "Shipped"),
    )

    order = models.OneToOneField("order.Order", on_delete=models.CASCADE, related_name="fulfilment_request")
    supplier = models.ForeignKey(
        FulfilmentSupplier, null=True, blank=True, on_delete=models.PROTECT,
        related_name="requests",
    )
    contact = models.ForeignKey(
        FulfilmentContact, null=True, blank=True, on_delete=models.PROTECT,
        related_name="requests",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_AWAITING_REVIEW)
    special_instructions = models.TextField(default=DEFAULT_FULFILMENT_INSTRUCTIONS)
    request_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Fulfilment request for {self.order.number}"
