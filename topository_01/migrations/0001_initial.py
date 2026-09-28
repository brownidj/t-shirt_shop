from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DesignRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("idea", models.CharField(max_length=200)),
                ("details", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
