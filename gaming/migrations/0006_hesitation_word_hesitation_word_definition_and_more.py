# Generated by Django 5.0.4 on 2025-01-05 09:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gaming", "0005_problem"),
    ]

    operations = [
        migrations.CreateModel(
            name="Hesitation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("duration", models.DurationField()),
                ("created_time", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "hesitation",
            },
        ),
        migrations.CreateModel(
            name="Word",
            fields=[
                (
                    "word",
                    models.CharField(
                        max_length=256, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("level", models.IntegerField()),
                (
                    "hesitations",
                    models.ManyToManyField(
                        blank=True,
                        through="gaming.Hesitation",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "word",
            },
        ),
        migrations.AddField(
            model_name="hesitation",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="gaming.word"
            ),
        ),
        migrations.CreateModel(
            name="Definition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("definition", models.CharField(max_length=256)),
                ("part_of_speech", models.CharField(max_length=256)),
                ("example", models.CharField(max_length=256)),
                ("translation", models.CharField(max_length=256)),
                (
                    "word",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="gaming.word"
                    ),
                ),
            ],
            options={
                "db_table": "definition",
            },
        ),
        migrations.AddField(
            model_name="problem",
            name="word",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="gaming.word",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="hesitations",
            field=models.ManyToManyField(
                blank=True, through="gaming.Hesitation", to="gaming.word"
            ),
        ),
    ]