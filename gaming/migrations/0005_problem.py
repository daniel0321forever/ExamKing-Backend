# Generated by Django 5.0.4 on 2024-12-14 14:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gaming", "0004_user_google_username_alter_user_email_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Problem",
            fields=[
                (
                    "hashed_id",
                    models.CharField(max_length=256, primary_key=True, serialize=False),
                ),
                (
                    "field",
                    models.CharField(
                        choices=[
                            ("Nursing", "nursing"),
                            ("Sanrio", "sanrio"),
                            ("biology", "biology"),
                        ],
                        max_length=32,
                    ),
                ),
                ("problem", models.CharField(max_length=512)),
                ("answer", models.IntegerField()),
                ("options", models.JSONField()),
                ("correct_rate", models.FloatField(default=60.0)),
            ],
            options={
                "db_table": "problem",
            },
        ),
    ]
