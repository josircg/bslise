# Generated by Django 3.2.25 on 2025-01-11 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20230219_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activationtask',
            name='task_kwargs',
            field=models.JSONField(verbose_name='Task Parameters'),
        ),
    ]
