# Generated by Django 5.2.1 on 2025-06-28 17:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("userprofile", "0022_remove_personal_info"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="birthdate",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="location",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="profession",
        ),
    ]
