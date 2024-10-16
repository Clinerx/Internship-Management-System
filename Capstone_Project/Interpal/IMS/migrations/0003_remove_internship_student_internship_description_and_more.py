# Generated by Django 5.1.1 on 2024-10-15 03:56

import datetime
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS', '0002_internship'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='internship',
            name='student',
        ),
        migrations.AddField(
            model_name='internship',
            name='description',
            field=models.TextField(default='Internship opportunity with exciting responsibilities and growth potential.'),
        ),
        migrations.AddField(
            model_name='internship',
            name='end_date',
            field=models.DateField(default=datetime.datetime(2024, 10, 15, 3, 56, 15, 948663, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AddField(
            model_name='internship',
            name='requirements',
            field=models.TextField(default='Basic requirements for the internship role.'),
        ),
        migrations.AddField(
            model_name='internship',
            name='start_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='internship',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internships', to='IMS.organization'),
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_name', models.CharField(max_length=255)),
                ('student_email', models.EmailField(max_length=254)),
                ('resume', models.FileField(upload_to='resumes/')),
                ('date_applied', models.DateTimeField(auto_now_add=True)),
                ('internship', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='IMS.internship')),
            ],
        ),
    ]