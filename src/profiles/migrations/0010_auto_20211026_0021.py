# Generated by Django 2.2.13 on 2021-10-26 00:21

from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0009_auto_20210219_1235'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='longitude',
        ),
        migrations.AddField(
            model_name='profile',
            name='contentVisible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='digest',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='profileVisible',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, max_length=2000, null=True, verbose_name='Short Bio and disciplinary background'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='orcid',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='ORCID (If you have registered on the ORCID platform for researchers and havea persistent digital identifier (your ORCID iD) you can add it here to link thisprofile with your professional information such as affiliations, grants, publications,peer review, and more.)'),
        ),
    ]
