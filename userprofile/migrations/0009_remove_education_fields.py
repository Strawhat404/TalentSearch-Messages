# Generated by Django 5.2.1 on 2025-06-14 23:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "userprofile",
            "0008_choices_delete_choicedata_delete_professionalchoices_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="education",
            name="gpa",
        ),
        migrations.RemoveField(
            model_name="education",
            name="graduation_year",
        ),
    ]
