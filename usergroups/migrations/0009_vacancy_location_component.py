# Generated by Django 3.0.9 on 2020-08-12 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usergroups', '0008_auto_20200812_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='location_component',
            field=models.CharField(choices=[('country', 'Land'), ('state', 'Bundesland'), ('county', 'Landkreis'), ('city', 'Stadt')], default='city', max_length=40),
        ),
    ]
