from __future__ import annotations

import logging
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import TYPE_CHECKING, ClassVar

import discord
from discord import app_commands
from discord.ext import commands, tasks
from django.utils import timezone

from bd_models.models import Ball, BallInstance, Player
from bd_models.models import balls as balls_cache
from reward.models import PlayerRewardClaim, PlayerRewardNotification, RewardConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("ballsdex.packages.reward")
Interaction = discord.Interaction["BallsDexBot"]

COOLDOWNS: dict[str, timedelta] = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}

REWARD_LABELS: dict[str, str] = {
    "daily": "Daily",
    "weekly": "Weekly",
    "monthly": "Monthly",
}


def _make_claim_callback(cog: "RewardCog", rtype: str):
    """Factory so each callback captures its own rtype without leaking it as a parameter."""
    async def _claim(interaction: Interaction):
        await cog._do_claim(interaction, rtype)
    return _claim


def make_reward_group(cog: "RewardCog", enabled_types: set[str]) -> app_commands.Group:
    """
    Build the /reward command group with only the enabled subcommands.
    Called once per setup() so each reload starts clean.
    """
    group = app_commands.Group(
        name="reward",
        description="Claim daily, weekly and monthly rewards.",
    )

    for rtype in ("daily", "weekly", "monthly"):
        if rtype not in enabled_types:
            continue
        label = REWARD_LABELS[rtype]

        cmd = app_commands.Command(
            name=rtype,
            callback=_make_claim_callback(cog, rtype),
            description=f"Claim your {label.lower()} reward.",
            parent=None,
            guild_ids=None,
            auto_locale_strings=True,
        )
        group.add_command(cmd)

    @group.command(
        name="notification",
        description="Get a DM the moment each reward cooldown expires.",
    )
    @app_commands.describe(toggle="Turn reward notifications on or off")
    @app_commands.choices(
        toggle=[
            app_commands.Choice(name="on", value="on"),
            app_commands.Choice(name="off", value="off"),
        ]
    )
    async def notification(interaction: Interaction, toggle: str):
        await cog._notification(interaction, toggle)

    return group


async def get_or_create_player(discord_id: int) -> Player:
    player, _ = await Player.objects.aget_or_create(discord_id=discord_id)
    return player


class RewardCog(commands.Cog, name="RewardCog"):
    """Daily, weekly and monthly collectible rewards."""

    _executor: ClassVar[ThreadPoolExecutor] = ThreadPoolExecutor()

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    async def cog_load(self):
        self._notification_task.start()

    async def cog_unload(self):
        self._notification_task.cancel()

    # ── Notification task ──────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def _notification_task(self):
        try:
            await self._send_ready_notifications()
        except Exception:
            log.exception("Error in reward notification task")

    @_notification_task.before_loop
    async def _before_notification(self):
        await self.bot.wait_until_ready()

    async def _send_ready_notifications(self):
        now = timezone.now()

        enabled_types: list[str] = [
            r
            async for r in RewardConfig.objects.filter(enabled=True)
            .values_list("reward_type", flat=True)
            .aiterator()
        ]
        if not enabled_types:
            return

        async for claim in (
            PlayerRewardClaim.objects.filter(
                notified=False, reward_type__in=enabled_types
            )
            .select_related("player")
            .aiterator()
        ):
            cooldown = COOLDOWNS.get(claim.reward_type)
            if not cooldown:
                continue
            if now < claim.claimed_at + cooldown:
                continue

            try:
                await PlayerRewardNotification.objects.aget(
                    player=claim.player, enabled=True
                )
            except PlayerRewardNotification.DoesNotExist:
                continue

            claim.notified = True
            await claim.asave(update_fields=["notified"])

            label = REWARD_LABELS.get(claim.reward_type, claim.reward_type.capitalize())
            try:
                user = await self.bot.fetch_user(claim.player.discord_id)
                await user.send(
                    f"⏰ Your **{label}** reward is ready to claim!\n"
                    f"Use `/reward {claim.reward_type}` to collect it now."
                )
                log.info(
                    f"Sent {label} reward notification to {claim.player.discord_id}"
                )
            except discord.HTTPException:
                pass

    # ── Shared claim logic ─────────────────────────────────────────────────────

    async def _do_claim(self, interaction: Interaction, reward_type: str):
        await interaction.response.defer(ephemeral=True)

        label = REWARD_LABELS[reward_type]
        cooldown = COOLDOWNS[reward_type]

        try:
            config = await RewardConfig.objects.aget(reward_type=reward_type, enabled=True)
        except RewardConfig.DoesNotExist:
            await interaction.followup.send(
                f"The **{label}** reward is currently disabled.", ephemeral=True
            )
            return

        player = await get_or_create_player(interaction.user.id)
        now = timezone.now()

        try:
            claim = await PlayerRewardClaim.objects.aget(
                player=player, reward_type=reward_type
            )
            next_claim = claim.claimed_at + cooldown
            if now < next_claim:
                await interaction.followup.send(
                    f"⏳ You already claimed your **{label}** reward!\n"
                    f"Come back {discord.utils.format_dt(next_claim, 'R')}.",
                    ephemeral=True,
                )
                return
        except PlayerRewardClaim.DoesNotExist:
            claim = None

        eligible = [
            b
            for b in balls_cache.values()
            if b.enabled and config.min_rarity <= b.rarity <= config.max_rarity
        ]
        if not eligible:
            eligible = [b for b in balls_cache.values() if b.enabled]
        if not eligible:
            await interaction.followup.send(
                "No collectibles are available for this reward right now. "
                "Please contact an admin!",
                ephemeral=True,
            )
            return

        ball = random.choice(eligible)

        instance = await BallInstance.objects.acreate(
            player=player,
            ball=ball,
            attack_bonus=random.randint(-20, 20),
            health_bonus=random.randint(-20, 20),
        )

        if claim:
            claim.claimed_at = now
            claim.notified = False
            claim.ball_instance = instance
            await claim.asave(update_fields=["claimed_at", "notified", "ball_instance"])
        else:
            await PlayerRewardClaim.objects.acreate(
                player=player,
                reward_type=reward_type,
                claimed_at=now,
                notified=False,
                ball_instance=instance,
            )

        log.info(
            f"Player {player.discord_id} claimed {label} reward: "
            f"{ball.country} (instance #{instance.pk})"
        )

        days = cooldown.days
        hours = int(cooldown.total_seconds() // 3600)
        time_str = (
            f"{days} day{'s' if days != 1 else ''}"
            if days >= 1
            else f"{hours} hour{'s' if hours != 1 else ''}"
        )

        content = f"🎁 You received **{ball.country}**! Come back in {time_str} for your next {label.lower()} reward."

        try:
            buffer = await interaction.client.loop.run_in_executor(
                self._executor, instance.draw_card
            )
            await interaction.followup.send(
                content=content,
                file=discord.File(buffer, "card.webp"),
                ephemeral=True,
            )
        except Exception:
            log.warning("Could not draw card for reward claim", exc_info=True)
            await interaction.followup.send(content=content, ephemeral=True)

    # ── Notification toggle ────────────────────────────────────────────────────

    async def _notification(self, interaction: Interaction, toggle: str):
        await interaction.response.defer(ephemeral=True)

        player = await get_or_create_player(interaction.user.id)
        enabled = toggle == "on"

        await PlayerRewardNotification.objects.aupdate_or_create(
            player=player,
            defaults={"enabled": enabled},
        )

        if enabled:
            await interaction.followup.send(
                "🔔 Reward notifications **enabled**!\n"
                "I'll DM you the moment your daily, weekly and monthly rewards "
                "are ready to claim.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "🔕 Reward notifications **disabled**.",
                ephemeral=True,
            )
