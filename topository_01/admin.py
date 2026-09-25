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
