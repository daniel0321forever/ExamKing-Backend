# Generated by Django 5.0.4 on 2025-01-05 09:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gaming", "0006_hesitation_word_hesitation_word_definition_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="definition",
            name="definition",
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name="definition",
            name="example",
            field=models.CharField(max_length=1024),
        ),
    ]
