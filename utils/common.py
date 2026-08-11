from __future__ import annotations
import discord
from config import EMBED_FOOTER


def base_embed(title: str, description: str = "", *, ok: bool | None = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=description)
    embed.set_footer(text=EMBED_FOOTER)
    return embed


def truncate(text: str, length: int = 3900) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def channel_type_name(channel: discord.abc.GuildChannel) -> str:
    if isinstance(channel, discord.TextChannel):
        return "text"
    if isinstance(channel, discord.VoiceChannel):
        return "voice"
    if isinstance(channel, discord.StageChannel):
        return "stage"
    if isinstance(channel, discord.ForumChannel):
        return "forum"
    if isinstance(channel, discord.CategoryChannel):
        return "category"
    return str(channel.type)
