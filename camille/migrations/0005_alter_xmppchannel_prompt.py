# Generated by Django 5.0.6 on 2024-07-24 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("camille", "0004_rename__prompt_xmppchannel_prompt_delete_xmppmessage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="xmppchannel",
            name="prompt",
            field=models.TextField(blank=True, default=""),
        ),
    ]
