# Generated by Django 3.0.9 on 2020-08-05 19:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=150)),
                ('image', models.ImageField(upload_to='images/%Y/%m/%d/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('members', models.ManyToManyField(related_name='activities', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
