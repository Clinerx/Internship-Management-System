# Generated by Django 5.0.2 on 2024-12-05 02:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS', '0013_remove_organization_barangay_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_approved', models.BooleanField(default=False)),
                ('approval_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='IMS.organization')),
            ],
        ),
    ]
