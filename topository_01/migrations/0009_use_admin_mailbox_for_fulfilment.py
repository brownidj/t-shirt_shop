from django.db import migrations


INVOICE_ADDRESS = "admin@topository.org"


def use_admin_mailbox_for_fulfilment(apps, schema_editor):
    Request = apps.get_model("topository_01", "FulfilmentRequest")
    instruction = (
        "Please send a finished T-shirt design preview to Topository for approval before production.\n\n"
        "Send the finished product by normal delivery directly to the shopper's address below.\n\n"
        f"Send the invoice to Topository at {INVOICE_ADDRESS} only. Do not include supplier pricing, "
        "invoice details, or supplier correspondence in any shopper communication or delivery."
    )
    Request.objects.filter(supplier__name="Garment Printing Group").update(
        special_instructions=instruction
    )


class Migration(migrations.Migration):
    dependencies = [("topository_01", "0008_link_gpg_partner_and_consolidate_legacy_partners")]

    operations = [migrations.RunPython(use_admin_mailbox_for_fulfilment, migrations.RunPython.noop)]
