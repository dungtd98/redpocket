# Generated by Django 5.1 on 2024-09-05 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_customuser_refcode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='invited_refcode',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
