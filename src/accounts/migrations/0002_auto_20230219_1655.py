# Generated by Django 2.2.28 on 2023-02-19 19:55

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='activationtask',
            name='task_description',
            field=models.CharField(default='', max_length=100, verbose_name='Task Description'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='activationtask',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='Task Email'),
        ),
        migrations.AlterField(
            model_name='activationtask',
            name='task_kwargs',
            field=django.contrib.postgres.fields.jsonb.JSONField(verbose_name='Task Params'),
        ),
        migrations.AlterField(
            model_name='activationtask',
            name='task_module',
            field=models.CharField(max_length=100, verbose_name='Task Module'),
        ),
        migrations.AlterField(
            model_name='activationtask',
            name='task_name',
            field=models.CharField(max_length=100, verbose_name='Task Name'),
        ),
        migrations.AlterUniqueTogether(
            name='activationtask',
            unique_together={('email', 'task_module', 'task_name', 'task_kwargs')},
        ),
    ]
