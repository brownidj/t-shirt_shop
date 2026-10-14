from django.db import migrations, models
import django.db.models.deletion


LEGACY_PARTNER_NAMES = ("topository Fulfilment", "Topository Fulfilment")


def consolidate_legacy_partners(apps, schema_editor):
    Partner = apps.get_model("partner", "Partner")
    PartnerAddress = apps.get_model("partner", "PartnerAddress")
    StockRecord = apps.get_model("partner", "StockRecord")
    OrderLine = apps.get_model("order", "Line")
    Supplier = apps.get_model("topository_01", "FulfilmentSupplier")
    Country = apps.get_model("address", "Country")

    supplier = Supplier.objects.get(name="Garment Printing Group")
    partner, _ = Partner.objects.get_or_create(name="Garment Printing Group")
    supplier.partner = partner
    supplier.save(update_fields=("partner",))

    # GPG belongs in Oscar's Fulfilment > Partners list as well as in the
    # fulfilment-supplier configuration.  This is GPG's operational address;
    # Topository's legacy personal address is deliberately not reused.
    australia, _ = Country.objects.get_or_create(
        iso_3166_1_a2="AU",
        defaults={
            "iso_3166_1_a3": "AUS",
            "iso_3166_1_numeric": "036",
            "printable_name": "Australia",
            "name": "Australia",
        },
    )
    PartnerAddress.objects.update_or_create(
        partner=partner,
        line1="2/7 Anella Avenue",
        defaults={
            "line2": "",
            "line3": "",
            "line4": "Castle Hill",
            "state": "NSW",
            "postcode": "2154",
            "country": australia,
            "search_text": "Garment Printing Group 2/7 Anella Avenue Castle Hill NSW 2154 Australia",
        },
    )

    legacy_partners = Partner.objects.filter(name__in=LEGACY_PARTNER_NAMES).exclude(
        pk=partner.pk
    )
    for legacy_partner in legacy_partners:
        for record in StockRecord.objects.filter(partner=legacy_partner).order_by("pk"):
            if StockRecord.objects.filter(
                partner=partner, partner_sku=record.partner_sku
            ).exists():
                # Historic product variants can share an SKU across the two
                # old placeholders. Retain both records safely without
                # discarding a product or violating Oscar's uniqueness rule.
                record.partner_sku = f"{record.partner_sku[:110]}-legacy-{record.pk}"
            record.partner = partner
            record.save(update_fields=("partner", "partner_sku"))
        OrderLine.objects.filter(partner=legacy_partner).update(partner=partner)
        # The legacy partner address and user link describe Topository, not
        # GPG; they must not be transferred to the external supplier.
        legacy_partner.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("partner", "0006_auto_20200724_0909"),
        ("order", "0020_alter_order_analytics_tracked"),
        ("topository_01", "0007_supplier_operational_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="partner",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fulfilment_supplier",
                to="partner.partner",
            ),
        ),
        migrations.RunPython(consolidate_legacy_partners, migrations.RunPython.noop),
    ]
