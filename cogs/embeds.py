from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.common import base_embed
from utils.db import save_changelog

class Embeds(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="embed_senden",description="Sendet eine saubere DEV-Embed-Nachricht.")
    async def embed_send(self,interaction:discord.Interaction,channel:discord.TextChannel,titel:str,text:str):
        if not await ensure_dev(interaction): return
        e=base_embed(titel,text); e.set_author(name=str(interaction.user),icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=e)
        await interaction.response.send_message(f"✅ Embed in {channel.mention} gesendet.",ephemeral=True)

    @app_commands.command(name="changelog",description="Veröffentlicht und speichert eine Server-Änderung.")
    async def changelog(self,interaction:discord.Interaction,channel:discord.TextChannel,titel:str,text:str):
        if not await ensure_dev(interaction): return
        save_changelog(interaction.guild_id,titel,text,interaction.user.id)
        e=base_embed(f"🆕 {titel}",text); e.set_author(name=str(interaction.user),icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=e)
        await interaction.response.send_message("✅ Changelog veröffentlicht.",ephemeral=True)

async def setup(bot): await bot.add_cog(Embeds(bot))
