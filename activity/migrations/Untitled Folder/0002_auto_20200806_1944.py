# Generated by Django 3.0.9 on 2020-08-06 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'verbose_name': 'Aktivität', 'verbose_name_plural': 'Aktivitäten'},
        ),
        migrations.AlterField(
            model_name='activity',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
