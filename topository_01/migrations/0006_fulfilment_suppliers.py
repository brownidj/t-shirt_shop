from django.db import migrations, models
import django.db.models.deletion


DEFAULT_FULFILMENT_INSTRUCTIONS = """Please send a finished T-shirt design preview to Topository for approval before production.

Send the finished product by normal delivery directly to the shopper's address below.

Send the invoice to Topository at info@tshirts.topository.org only. Do not include supplier pricing, invoice details, or supplier correspondence in any shopper communication or delivery."""


def create_garment_printing_group(apps, schema_editor):
    Supplier = apps.get_model("topository_01", "FulfilmentSupplier")
    Contact = apps.get_model("topository_01", "FulfilmentContact")
    supplier, _ = Supplier.objects.update_or_create(
        name="Garment Printing Group",
        defaults={
            "supports_blind_shipping": True,
            "proof_required": True,
            "active": True,
        },
    )
    contacts = (
        ("Alastair", "alastair@garmentprinting.com.au", True),
        ("Alan", "alan@garmentprinting.com.au", False),
        ("Steve Shaw", "steve@garmentprinting.com.au", False),
    )
    for name, email, is_default in contacts:
        Contact.objects.update_or_create(
            supplier=supplier,
            email=email,
            defaults={"name": name, "is_default": is_default, "active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0020_alter_order_analytics_tracked"),
        ("topository_01", "0005_shorten_returns_flatpage_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="FulfilmentSupplier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
                ("supports_blind_shipping", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
                ("proof_required", models.BooleanField(default=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="FulfilmentContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("email", models.EmailField(max_length=254)),
                ("is_default", models.BooleanField(default=False)),
                ("active", models.BooleanField(default=True)),
                ("supplier", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="topository_01.fulfilmentsupplier")),
            ],
            options={"ordering": ("supplier", "name")},
        ),
        migrations.CreateModel(
            name="FulfilmentRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("awaiting_review", "Awaiting review"), ("request_sent", "Request sent"), ("proof_received", "Proof received"), ("approved", "Approved"), ("in_production", "In production"), ("shipped", "Shipped")], default="awaiting_review", max_length=32)),
                ("special_instructions", models.TextField(default=DEFAULT_FULFILMENT_INSTRUCTIONS)),
                ("request_sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contact", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="requests", to="topository_01.fulfilmentcontact")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="fulfilment_request", to="order.order")),
                ("supplier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="requests", to="topository_01.fulfilmentsupplier")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="fulfilmentcontact",
            constraint=models.UniqueConstraint(fields=("supplier", "email"), name="unique_fulfilment_contact_email"),
        ),
        migrations.RunPython(create_garment_printing_group, migrations.RunPython.noop),
    ]
