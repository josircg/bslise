# Generated by Django 2.2.10 on 2020-02-25 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='title',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Short Bio and disciplinary background'),
        ),
    ]
