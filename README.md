# BallsDex V3 Reward Package

Daily, weekly and monthly collectible reward commands for **BallsDex V3**. Players claim a random collectible on a cooldown — once per day, week, or month. Only commands enabled in the admin panel appear in Discord.

## Commands

| Command | Description |
|---|---|
| `/reward daily` | Claim a random collectible once every 24 hours |
| `/reward weekly` | Claim a random collectible once every 7 days |
| `/reward monthly` | Claim a random collectible once every 30 days |
| `/reward notification on` | Get a DM the moment each reward cooldown expires |
| `/reward notification off` | Stop DM notifications |

## Installation

### 1 — Configure extra.toml

**If the file doesn't exist:** Create a new file `extra.toml` in your `config` folder under the BallsDex directory.

**If you already have other packages installed:** Simply add the following configuration to your existing `extra.toml` file. Each package is defined by a `[[ballsdex.packages]]` section, so you can have multiple packages installed.

Add the following configuration:

```toml
[[ballsdex.packages]]
location = "git+https://github.com/faye69/BallsDex-Reward-Pack.git"
path = "reward"
enabled = true
editable = false
```

**Example of multiple packages:**

```toml
# First package
[[ballsdex.packages]]
location = "git+https://github.com/example/other-package.git"
path = "other"
enabled = true
editable = false

# Reward Package
[[ballsdex.packages]]
location = "git+https://github.com/faye69/BallsDex-Reward-Pack.git"
path = "reward"
enabled = true
editable = false
```

### 2 — Rebuild and start the bot

```bash
docker compose build
docker compose up -d
```

## Admin Panel Setup

Go to **Reward → Reward Configs** and create an entry for each command you want enabled:

| Field | Description |
|---|---|
| Reward type | `daily`, `weekly`, or `monthly` |
| Enabled | Tick to make the command visible and usable in Discord |
| Min rarity | Lower bound of the rarity range (higher value = more common) |
| Max rarity | Upper bound of the rarity range (higher value = more common) |

Create entries only for the types you want. Any type with no entry will simply not appear in Discord.

### Applying changes without a full restart

After toggling a reward type on or off in the admin panel, reload the package and sync:

```
@YourBot reload reward.reward
@YourBot reloadtree
```

This updates the command list in Discord within seconds.
Rarity range changes (`min_rarity` / `max_rarity`) take effect on the next claim with no reload needed.

## Admin Panel — Reward Claims

Under **Reward → Player Reward Claims** you can see every player's last claim per reward type, including:

- **Player** — Discord ID
- **Reward type** — daily / weekly / monthly
- **Ball received** — the collectible the player got on their last claim
- **Claimed at** — timestamp of the last claim
- **Notified** — whether the cooldown-ready DM has been sent for this cycle

## Notifications

Players opt in with `/reward notification on`. The bot DMs them exactly when each cooldown expires. No spam — one DM per reward per cycle, sent the moment it becomes claimable.
