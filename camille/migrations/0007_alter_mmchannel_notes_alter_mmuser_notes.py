# Generated by Django 5.2.1 on 2025-05-13 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "camille",
            "0006_alter_mmchannel_display_name_alter_mmchannel_header_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="mmchannel",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="mmuser",
            name="notes",
            field=models.TextField(blank=True),
        ),
    ]
