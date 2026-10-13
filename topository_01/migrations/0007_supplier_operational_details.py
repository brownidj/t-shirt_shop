from django.db import migrations, models


def add_gpg_operational_details(apps, schema_editor):
    Supplier = apps.get_model("topository_01", "FulfilmentSupplier")
    Supplier.objects.filter(name="Garment Printing Group").update(
        address="2/7 Anella Avenue\nCastle Hill NSW 2154\nAustralia",
        sales_email="sales@garmentprinting.com.au",
        support_email="support@garmentprinting.com.au",
        phone_number="1300 986 000",
        opening_hours="Mon–Fri: 9 am – 3 pm; Sat–Sun: Closed",
    )


class Migration(migrations.Migration):
    dependencies = [("topository_01", "0006_fulfilment_suppliers")]

    operations = [
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="address",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="opening_hours",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="phone_number",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="sales_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="fulfilmentsupplier",
            name="support_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.RunPython(add_gpg_operational_details, migrations.RunPython.noop),
    ]
