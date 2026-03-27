from django.apps import AppConfig


class RewardApp(AppConfig):
    name = "reward"
    verbose_name = "Reward"
    default_auto_field = "django.db.models.BigAutoField"
    dpy_package = "reward.reward"
