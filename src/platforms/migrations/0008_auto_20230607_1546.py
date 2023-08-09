# Generated by Django 2.2.28 on 2023-06-07 18:46
from django.core.validators import EMPTY_VALUES
from django.db import migrations


def load_geographic_extend(apps, schema_editor):
    """Adds GeographicExtend and update Platform corresponding geographicExtend"""


class Migration(migrations.Migration):
    dependencies = [
        ('platforms', '0007_auto_20230607_1546'),
    ]

    operations = [
        migrations.RunPython(load_geographic_extend)
    ]
