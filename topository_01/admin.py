from django.contrib import admin
from oscar.core.loading import get_model

# Use Oscar's through model for Partner↔User links.
Partner = get_model('partner', 'Partner')
PartnerUserLink = Partner.users.through

@admin.register(PartnerUserLink)
class PartnerUserLinkAdmin(admin.ModelAdmin):
    list_display = ("partner", "user")
    list_filter = ("partner",)
    search_fields = ("user__username", "user__email", "partner__name")
from django.contrib import admin

from .models import (
    DesignRequest,
    FulfilmentContact,
    FulfilmentRequest,
    FulfilmentSupplier,
)


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    list_display = ("idea", "name", "email", "created_at")
    search_fields = ("idea", "name", "email", "details")
    readonly_fields = ("created_at",)


class FulfilmentContactInline(admin.TabularInline):
    model = FulfilmentContact
    extra = 0


@admin.register(FulfilmentSupplier)
class FulfilmentSupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name", "sales_email", "phone_number", "supports_blind_shipping",
        "proof_required", "active",
    )
    list_filter = ("supports_blind_shipping", "proof_required", "active")
    search_fields = ("name", "sales_email", "support_email")
    inlines = (FulfilmentContactInline,)


@admin.register(FulfilmentRequest)
class FulfilmentRequestAdmin(admin.ModelAdmin):
    list_display = ("order", "supplier", "contact", "status", "request_sent_at")
    list_filter = ("status", "supplier")
    search_fields = ("order__number", "supplier__name", "contact__name")
    readonly_fields = ("created_at", "updated_at", "request_sent_at")
