from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfessionalChoices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_sizes', models.JSONField(default=list)),
                ('industries', models.JSONField(default=list)),
                ('leadership_styles', models.JSONField(default=list)),
                ('communication_styles', models.JSONField(default=list)),
                ('motivations', models.JSONField(default=list)),
            ],
            options={
                'verbose_name': 'Professional Choices',
                'verbose_name_plural': 'Professional Choices',
            },
        ),
        migrations.AlterField(
            model_name='professionalqualifications',
            name='preferred_company_size',
            field=models.CharField(choices=[], help_text='Preferred company size', max_length=50),
        ),
        migrations.AlterField(
            model_name='professionalqualifications',
            name='preferred_industry',
            field=models.CharField(choices=[], help_text='Preferred industry', max_length=50),
        ),
        migrations.AlterField(
            model_name='professionalqualifications',
            name='leadership_style',
            field=models.CharField(choices=[], help_text='Leadership style', max_length=50),
        ),
        migrations.AlterField(
            model_name='professionalqualifications',
            name='communication_style',
            field=models.CharField(choices=[], help_text='Communication style', max_length=50),
        ),
        migrations.AlterField(
            model_name='professionalqualifications',
            name='motivation',
            field=models.CharField(choices=[], help_text='Motivation', max_length=50),
        ),
    ]
