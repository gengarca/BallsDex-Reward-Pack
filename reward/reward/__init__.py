from discord.ext import commands


async def setup(bot: commands.Bot):
    from reward.models import RewardConfig
    from .cog import RewardCog, make_reward_group

    enabled_types: set[str] = {
        rt
        async for rt in (
            RewardConfig.objects.filter(enabled=True)
            .values_list("reward_type", flat=True)
            .aiterator()
        )
    }

    cog = RewardCog(bot)
    group = make_reward_group(cog, enabled_types)
    bot.tree.add_command(group)
    await bot.add_cog(cog)


async def teardown(bot: commands.Bot):
    bot.tree.remove_command("reward")
    bot.remove_cog("RewardCog")
