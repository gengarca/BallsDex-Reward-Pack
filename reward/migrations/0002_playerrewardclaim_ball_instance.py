import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bd_models", "0014_alter_ball_options_alter_ballinstance_options_and_more"),
        ("reward", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playerrewardclaim",
            name="ball_instance",
            field=models.ForeignKey(
                blank=True,
                help_text="The collectible instance the player received on their last claim.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reward_claims",
                to="bd_models.ballinstance",
            ),
        ),
    ]
