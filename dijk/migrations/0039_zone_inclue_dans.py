# Generated by Django 4.0.5 on 2023-02-11 20:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0038_lieu_autre_nom'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='inclue_dans',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_manager_sous_zones', to='dijk.zone'),
        ),
    ]