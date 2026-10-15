from django.db import migrations, models


INSTRUCTIONS = """Please send a finished T-shirt design preview to Topository for approval before production.

Send the finished product by normal delivery directly to the shopper's address below.

Send the invoice to Topository at admin@topository.org only. Do not include supplier pricing, invoice details, or supplier correspondence in any shopper communication or delivery."""


class Migration(migrations.Migration):
    dependencies = [("topository_01", "0009_use_admin_mailbox_for_fulfilment")]

    operations = [
        migrations.AlterField(
            model_name="fulfilmentrequest",
            name="special_instructions",
            field=models.TextField(default=INSTRUCTIONS),
        ),
    ]
