# Generated by Django 5.2 on 2025-06-25 16:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("adverts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="advert",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Advert",
                "verbose_name_plural": "Adverts",
            },
        ),
    ]
