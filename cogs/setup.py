from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.db import set_setting, all_settings
from utils.common import base_embed

class Setup(commands.Cog):
    def __init__(self, bot): self.bot = bot

    setup_group = app_commands.Group(name="setup", description="DEV-Bot Einstellungen")

    @setup_group.command(name="anzeigen", description="Zeigt alle gespeicherten Bot-Einstellungen.")
    async def show(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        data = all_settings(interaction.guild_id)
        if not data:
            await interaction.response.send_message("Noch keine dynamischen Einstellungen gesetzt.", ephemeral=True); return
        text = "\n".join(f"**{k}** → `{v}`" for k,v in sorted(data.items()))
        await interaction.response.send_message(embed=base_embed("⚙️ Setup", text), ephemeral=True)

    @setup_group.command(name="log_channel", description="Setzt den Channel für DEV-Logs.")
    async def log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await ensure_dev(interaction): return
        set_setting(interaction.guild_id, "log_channel_id", channel.id)
        await interaction.response.send_message(f"✅ Log-Channel: {channel.mention}", ephemeral=True)

    @setup_group.command(name="archiv", description="Setzt die Kategorie für archivierte Projekte.")
    async def archive(self, interaction: discord.Interaction, kategorie: discord.CategoryChannel):
        if not await ensure_dev(interaction): return
        set_setting(interaction.guild_id, "archive_category_id", kategorie.id)
        await interaction.response.send_message(f"✅ Archiv: **{kategorie.name}**", ephemeral=True)

    @setup_group.command(name="backup_channel", description="Setzt optional einen Channel für Backup-Dateien.")
    async def backup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await ensure_dev(interaction): return
        set_setting(interaction.guild_id, "backup_channel_id", channel.id)
        await interaction.response.send_message(f"✅ Backup-Channel: {channel.mention}", ephemeral=True)

async def setup(bot): await bot.add_cog(Setup(bot))
