# Generated by Django 4.0.5 on 2022-12-29 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0032_remove_lieu_adresse_ville_lieux_calculés_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupeTypeLieu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('type_lieu', models.ManyToManyField(to='dijk.typelieu')),
            ],
        ),
    ]