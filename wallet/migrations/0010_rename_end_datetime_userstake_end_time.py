# Generated by Django 5.1 on 2024-08-29 04:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0009_userstake_created_at'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userstake',
            old_name='end_datetime',
            new_name='end_time',
        ),
    ]
