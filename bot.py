import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# ── Config ────────────────────────────────────────────────────
TOKEN = "YOUR_BOT_TOKEN_HERE"
DATA_FILE = "prefixes.json"

# ── Persistence ───────────────────────────────────────────────
def load_data() -> dict:
    """Returns dict of { "XX": {"name": "...", "owner": "..."} }"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            raw = json.load(f)
        # migrate old flat format {"XX": "name"} if needed
        migrated = {}
        for k, v in raw.items():
            if isinstance(v, str):
                migrated[k.upper()] = {"name": v, "owner": ""}
            else:
                migrated[k.upper()] = v
        return migrated

    # no prefixes yet — use /prefix-add to add nodes
    return {}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Grid renderer ─────────────────────────────────────────────
def render_grid(data: dict) -> str:
    used = set(data.keys())
    digits = list("0123456789ABCDEF")

    RED   = "\x1b[31;1m"
    RESET = "\x1b[0m"

    lines = ["    " + "  ".join(f" {c}" for c in digits)]
    lines.append("   " + "─" * 65)

    for r in digits:
        row = f"{r} │"
        for c in digits:
            key = r + c
            if key in used:
                row += f"{RED}[{key}]{RESET}"
            else:
                row += f" {key} "
        lines.append(row)

    lines.append("")
    lines.append(f"  {len(used)}/256 prefixes in use")

    return "```ansi\n" + "\n".join(lines) + "\n```"

# ── Helpers ───────────────────────────────────────────────────
def validate_prefix(prefix: str):
    p = prefix.upper().strip()
    if len(p) == 2 and all(c in "0123456789ABCDEF" for c in p):
        return p
    return None

# ── Bot setup ─────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user} — slash commands synced.")

# ── Commands ──────────────────────────────────────────────────

@tree.command(name="prefix-show", description="Show the MeshCore prefix grid")
async def prefix_show(interaction: discord.Interaction):
    data = load_data()
    await interaction.response.send_message(render_grid(data))


@tree.command(name="prefix-add", description="Mark a prefix as used")
@app_commands.describe(
    prefix="Two hex characters, e.g. C3",
    name="Node name, e.g. My Repeater",
    owner="Discord username of the node operator, e.g. @jake"
)
async def prefix_add(
    interaction: discord.Interaction,
    prefix: str,
    name: str,
    owner: str = ""
):
    p = validate_prefix(prefix)
    if not p:
        await interaction.response.send_message(
            f"❌ `{prefix}` isn't a valid 2-digit hex prefix.", ephemeral=True
        )
        return

    data = load_data()

    if p in data:
        await interaction.response.send_message(
            f"⚠️ `{p}` is already taken by **{data[p]['name']}**. "
            f"Use `/prefix-update` to change it.", ephemeral=True
        )
        return

    data[p] = {"name": name, "owner": owner.strip()}
    save_data(data)

    owner_str = f" (owner: {owner.strip()})" if owner.strip() else ""
    await interaction.response.send_message(
        f"✅ Added `{p}` → **{name}**{owner_str}\n\n{render_grid(data)}"
    )


@tree.command(name="prefix-remove", description="Free up a prefix")
@app_commands.describe(prefix="Two hex characters, e.g. C3")
async def prefix_remove(interaction: discord.Interaction, prefix: str):
    p = validate_prefix(prefix)
    if not p:
        await interaction.response.send_message(
            f"❌ `{prefix}` isn't a valid 2-digit hex prefix.", ephemeral=True
        )
        return

    data = load_data()
    if p not in data:
        await interaction.response.send_message(
            f"❌ `{p}` isn't in use.", ephemeral=True
        )
        return

    entry = data.pop(p)
    save_data(data)
    await interaction.response.send_message(
        f"🗑️ Removed `{p}` (was **{entry['name']}**)\n\n{render_grid(data)}"
    )


@tree.command(name="prefix-update", description="Update a prefix's name and/or owner")
@app_commands.describe(
    prefix="Two hex characters, e.g. C3",
    name="New node name (leave blank to keep current)",
    owner="New owner username (leave blank to keep current)"
)
async def prefix_update(
    interaction: discord.Interaction,
    prefix: str,
    name: str = "",
    owner: str = ""
):
    p = validate_prefix(prefix)
    if not p:
        await interaction.response.send_message(
            f"❌ `{prefix}` isn't a valid 2-digit hex prefix.", ephemeral=True
        )
        return

    data = load_data()
    if p not in data:
        await interaction.response.send_message(
            f"❌ `{p}` isn't in use. Use `/prefix-add` to add it.", ephemeral=True
        )
        return

    entry = data[p]
    changes = []

    if name.strip():
        changes.append(f"name: **{entry['name']}** → **{name.strip()}**")
        entry["name"] = name.strip()

    if owner.strip():
        old_owner = entry.get("owner") or "none"
        changes.append(f"owner: **{old_owner}** → **{owner.strip()}**")
        entry["owner"] = owner.strip()

    if not changes:
        await interaction.response.send_message(
            "⚠️ No changes provided — pass a new `name` and/or `owner`.", ephemeral=True
        )
        return

    data[p] = entry
    save_data(data)
    await interaction.response.send_message(
        f"✏️ Updated `{p}`: {', '.join(changes)}\n\n{render_grid(data)}"
    )


@tree.command(name="prefix-clear-owner", description="Remove the owner from a prefix")
@app_commands.describe(prefix="Two hex characters, e.g. C3")
async def prefix_clear_owner(interaction: discord.Interaction, prefix: str):
    p = validate_prefix(prefix)
    if not p:
        await interaction.response.send_message(
            f"❌ `{prefix}` isn't a valid 2-digit hex prefix.", ephemeral=True
        )
        return

    data = load_data()
    if p not in data:
        await interaction.response.send_message(
            f"❌ `{p}` isn't in use.", ephemeral=True
        )
        return

    old_owner = data[p].get("owner") or ""
    if not old_owner:
        await interaction.response.send_message(
            f"⚠️ `{p}` doesn't have an owner set.", ephemeral=True
        )
        return

    data[p]["owner"] = ""
    save_data(data)
    await interaction.response.send_message(
        f"✅ Cleared owner (**{old_owner}**) from `{p}` (**{data[p]['name']}**)"
    )


@tree.command(name="prefix-list", description="List all used prefixes, node names, and owners")
async def prefix_list(interaction: discord.Interaction):
    data = load_data()
    if not data:
        await interaction.response.send_message("No prefixes in use yet.")
        return

    lines = []
    for k in sorted(data.keys()):
        entry = data[k]
        owner_str = f" — {entry['owner']}" if entry.get("owner") else ""
        lines.append(f"`{k}` **{entry['name']}**{owner_str}")

    msg = f"**{len(data)}/256 prefixes in use:**\n" + "\n".join(lines)
    await interaction.response.send_message(msg)


bot.run(TOKEN)
