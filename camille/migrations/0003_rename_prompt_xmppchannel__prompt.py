# Generated by Django 5.0.6 on 2024-07-19 08:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("camille", "0002_xmppchannel_prompt"),
    ]

    operations = [
        migrations.RenameField(
            model_name="xmppchannel",
            old_name="prompt",
            new_name="_prompt",
        ),
    ]
