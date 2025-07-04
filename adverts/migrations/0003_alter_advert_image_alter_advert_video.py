# Generated by Django 5.2.1 on 2025-07-01 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adverts", "0002_alter_advert_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="advert",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Image for the advert",
                null=True,
                upload_to="media/adverts/images/",
            ),
        ),
        migrations.AlterField(
            model_name="advert",
            name="video",
            field=models.FileField(
                blank=True,
                help_text="Video for the advert",
                null=True,
                upload_to="media/adverts/videos/",
            ),
        ),
    ]
