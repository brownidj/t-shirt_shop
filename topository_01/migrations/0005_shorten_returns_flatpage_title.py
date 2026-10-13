from django.db import migrations


def shorten_returns_page_title(apps, schema_editor):
    flat_page = apps.get_model("flatpages", "FlatPage")
    flat_page.objects.filter(url="/returns-refunds-cancellations/").update(
        title="Returns & Refunds"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("topository_01", "0004_legal_flatpages"),
    ]

    operations = [migrations.RunPython(shorten_returns_page_title, migrations.RunPython.noop)]
