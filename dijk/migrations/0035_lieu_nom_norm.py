# Generated by Django 4.0.5 on 2023-01-23 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0034_groupetypelieu_féminin'),
    ]

    operations = [
        migrations.AddField(
            model_name='lieu',
            name='nom_norm',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
