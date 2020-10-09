# Generated by Django 3.0.9 on 2020-08-09 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0008_remove_activity_created'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Kategorie', 'verbose_name_plural': 'Kategorien'},
        ),
        migrations.AddField(
            model_name='activity',
            name='type',
            field=models.CharField(choices=[('competitive', 'kompetitiv'), ('creative', 'kreativ'), ('consumption', 'konsumorientiert')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='type',
            field=models.CharField(choices=[('competitive', 'kompetitiv'), ('creative', 'kreativ'), ('consumption', 'konsumorientiert')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='name',
            field=models.CharField(max_length=30, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/%Y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=30, null=True, unique=True),
        ),
    ]
