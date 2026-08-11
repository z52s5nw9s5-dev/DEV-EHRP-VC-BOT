from __future__ import annotations
import discord
from config import GUILD_ID, OWNER_USER_ID, DEV_ROLE_ID


def is_owner(user: discord.abc.User) -> bool:
    return user.id == OWNER_USER_ID


def is_dev_member(user: discord.abc.User) -> bool:
    if is_owner(user):
        return True
    return isinstance(user, discord.Member) and any(r.id == DEV_ROLE_ID for r in user.roles)


async def ensure_dev(interaction: discord.Interaction) -> bool:
    if interaction.guild_id != GUILD_ID:
        await interaction.response.send_message("❌ Dieser Bot ist nur für EHRP eingerichtet.", ephemeral=True)
        return False
    if not is_dev_member(interaction.user):
        await interaction.response.send_message("⛔ Keine DEV-Berechtigung.", ephemeral=True)
        return False
    return True


async def ensure_owner(interaction: discord.Interaction) -> bool:
    if interaction.user.id != OWNER_USER_ID:
        await interaction.response.send_message("⛔ Nur der Bot-Owner darf diese Funktion nutzen.", ephemeral=True)
        return False
    return True
