# Generated by Django 5.1.1 on 2024-10-23 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS', '0004_alter_organization_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='password',
            field=models.CharField(max_length=255),
        ),
    ]