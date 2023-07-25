# Generated by Django 2.2.28 on 2022-11-23 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0049_auto_20220916_1642'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingResource',
            fields=[
            ],
            options={
                'verbose_name': 'Training Resource',
                'verbose_name_plural': 'Training Resources',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('resources.resource',),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Resource Category'},
        ),
        migrations.AlterModelOptions(
            name='resource',
            options={'verbose_name': 'Resource'},
        ),
    ]
