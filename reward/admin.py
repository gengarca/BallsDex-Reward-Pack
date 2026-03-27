from django.contrib import admin

from .models import PlayerRewardClaim, PlayerRewardNotification, RewardConfig


@admin.register(RewardConfig)
class RewardConfigAdmin(admin.ModelAdmin):
    list_display = ["reward_type", "enabled", "min_rarity", "max_rarity"]
    list_editable = ["enabled", "min_rarity", "max_rarity"]
    ordering = ["reward_type"]


@admin.register(PlayerRewardClaim)
class PlayerRewardClaimAdmin(admin.ModelAdmin):
    list_display = ["player", "reward_type", "ball_received", "claimed_at", "notified"]
    list_filter = ["reward_type", "notified"]
    readonly_fields = ["player", "reward_type", "ball_instance", "claimed_at", "notified"]
    search_fields = ["player__discord_id", "ball_instance__ball__country"]
    ordering = ["-claimed_at"]
    list_select_related = True

    @admin.display(description="Ball received")
    def ball_received(self, obj):
        if obj.ball_instance_id is None:
            return "—"
        return obj.ball_instance.ball.country

    def has_add_permission(self, request):
        return False


@admin.register(PlayerRewardNotification)
class PlayerRewardNotificationAdmin(admin.ModelAdmin):
    list_display = ["player", "enabled"]
    list_filter = ["enabled"]
    search_fields = ["player__discord_id"]
