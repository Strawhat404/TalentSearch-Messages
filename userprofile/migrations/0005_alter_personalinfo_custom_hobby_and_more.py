# Generated by Django 5.2.1 on 2025-06-13 20:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("userprofile", "0004_alter_personalinfo_date_of_birth_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="personalinfo",
            name="custom_hobby",
            field=models.CharField(default="", max_length=100),
        ),
        migrations.AlterField(
            model_name="physicalattributes",
            name="height",
            field=models.DecimalField(
                decimal_places=1,
                default=100,
                help_text="Height in centimeters (required)",
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(
                        100, message="Height must be at least 100 cm"
                    ),
                    django.core.validators.MaxValueValidator(
                        300, message="Height cannot exceed 300 cm"
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="physicalattributes",
            name="weight",
            field=models.DecimalField(
                decimal_places=1,
                default=30,
                help_text="Weight in kilograms (required)",
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(
                        30, message="Weight must be at least 30 kg"
                    ),
                    django.core.validators.MaxValueValidator(
                        500, message="Weight cannot exceed 500 kg"
                    ),
                ],
            ),
        ),
    ]
