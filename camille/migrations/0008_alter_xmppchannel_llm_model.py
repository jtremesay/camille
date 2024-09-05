# Generated by Django 5.1.1 on 2024-09-05 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("camille", "0007_alter_xmppchannel_llm_model_xmppmessage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="xmppchannel",
            name="llm_model",
            field=models.CharField(
                choices=[
                    ("gemini-1.5-flash-latest", "Gemini Flash"),
                    ("gemini-1.5-pro-latest", "Gemini Pro"),
                ],
                default="gemini-1.5-flash-latest",
                max_length=64,
            ),
        ),
    ]
