# Generated by Django 5.0.8 on 2024-08-27 06:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_referral_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='user_level',
        ),
    ]
