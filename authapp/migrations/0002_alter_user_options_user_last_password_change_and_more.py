# Generated by Django 5.2 on 2025-05-23 09:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authapp", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={},
        ),
        migrations.AddField(
            model_name="user",
            name="last_password_change",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterModelTable(
            name="user",
            table="auth_user",
        ),
    ]
