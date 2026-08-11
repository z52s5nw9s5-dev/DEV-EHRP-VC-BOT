from __future__ import annotations
import discord
from utils.db import get_setting
from utils.common import base_embed


async def send_log(guild: discord.Guild, title: str, description: str) -> None:
    raw = get_setting(guild.id, "log_channel_id")
    if not raw:
        return
    channel = guild.get_channel(int(raw))
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(embed=base_embed(title, description))
    except discord.HTTPException:
        pass
