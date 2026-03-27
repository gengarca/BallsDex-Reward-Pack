import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bd_models", "0014_alter_ball_options_alter_ballinstance_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RewardConfig",
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
                (
                    "reward_type",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        max_length=10,
                        unique=True,
                    ),
                ),
                ("enabled", models.BooleanField(default=False)),
                ("min_rarity", models.FloatField(default=0.0)),
                ("max_rarity", models.FloatField(default=100.0)),
            ],
            options={
                "verbose_name": "Reward Config",
                "verbose_name_plural": "Reward Configs",
                "ordering": ["reward_type"],
            },
        ),
        migrations.CreateModel(
            name="PlayerRewardClaim",
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
                (
                    "reward_type",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        max_length=10,
                    ),
                ),
                ("claimed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("notified", models.BooleanField(default=False)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reward_claims",
                        to="bd_models.player",
                    ),
                ),
            ],
            options={
                "verbose_name": "Player Reward Claim",
                "verbose_name_plural": "Player Reward Claims",
                "ordering": ["-claimed_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="playerrewardclaim",
            unique_together={("player", "reward_type")},
        ),
        migrations.CreateModel(
            name="PlayerRewardNotification",
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
                ("enabled", models.BooleanField(default=False)),
                (
                    "player",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reward_notification",
                        to="bd_models.player",
                    ),
                ),
            ],
            options={
                "verbose_name": "Player Reward Notification",
                "verbose_name_plural": "Player Reward Notifications",
            },
        ),
    ]
