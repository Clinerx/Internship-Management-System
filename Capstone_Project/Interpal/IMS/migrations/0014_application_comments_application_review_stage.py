# Generated by Django 5.1.1 on 2024-10-30 06:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS', '0013_application_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='review_stage',
            field=models.CharField(default='Under Review', max_length=100),
        ),
    ]