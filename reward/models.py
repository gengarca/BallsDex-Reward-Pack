from django.db import models
from django.utils import timezone


REWARD_TYPES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
]


class RewardConfig(models.Model):
    reward_type = models.CharField(
        max_length=10,
        choices=REWARD_TYPES,
        unique=True,
        help_text="Which reward command this config controls.",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Tick to make this reward command visible and usable in Discord.",
    )
    min_rarity = models.FloatField(
        default=0.0,
        help_text="Minimum rarity value for eligible collectibles (higher = more common).",
    )
    max_rarity = models.FloatField(
        default=100.0,
        help_text="Maximum rarity value for eligible collectibles (higher = more common).",
    )

    class Meta:
        verbose_name = "Reward Config"
        verbose_name_plural = "Reward Configs"
        ordering = ["reward_type"]

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.get_reward_type_display()} Reward ({status})"


class PlayerRewardClaim(models.Model):
    player = models.ForeignKey(
        "bd_models.Player",
        on_delete=models.CASCADE,
        related_name="reward_claims",
    )
    reward_type = models.CharField(max_length=10, choices=REWARD_TYPES)
    claimed_at = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(
        default=False,
        help_text="Whether the cooldown-ready DM has been sent for the current cycle.",
    )
    ball_instance = models.ForeignKey(
        "bd_models.BallInstance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward_claims",
        help_text="The collectible instance the player received on their last claim.",
    )

    class Meta:
        unique_together = [("player", "reward_type")]
        verbose_name = "Player Reward Claim"
        verbose_name_plural = "Player Reward Claims"
        ordering = ["-claimed_at"]

    def __str__(self) -> str:
        return f"{self.player} — {self.reward_type} at {self.claimed_at:%Y-%m-%d %H:%M}"


class PlayerRewardNotification(models.Model):
    player = models.OneToOneField(
        "bd_models.Player",
        on_delete=models.CASCADE,
        related_name="reward_notification",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="If true, bot DMs this player when each reward cooldown expires.",
    )

    class Meta:
        verbose_name = "Player Reward Notification"
        verbose_name_plural = "Player Reward Notifications"

    def __str__(self) -> str:
        return f"{self.player} — notifications {'on' if self.enabled else 'off'}"
