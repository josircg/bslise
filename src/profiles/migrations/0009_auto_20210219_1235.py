# Generated by Django 2.2.13 on 2021-02-19 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0008_auto_20210218_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='organisation',
            field=models.ManyToManyField(blank=True, to='organisations.Organisation'),
        ),
    ]
