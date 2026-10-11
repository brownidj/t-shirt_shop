from django.db import migrations


def set_default_first_names(apps, schema_editor):
    user_model = apps.get_model("auth", "User")

    for user in user_model.objects.only("pk", "first_name").iterator():
        if not (user.first_name or "").strip():
            user.first_name = "Shopper"
            user.save(update_fields=["first_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("topository_01", "0002_marketingconsent"),
    ]

    operations = [
        migrations.RunPython(set_default_first_names, migrations.RunPython.noop),
    ]
