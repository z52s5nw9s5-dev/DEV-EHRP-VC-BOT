from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.common import base_embed

class Core(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="dev", description="Öffnet die komplette DEV-Übersicht.")
    async def dev(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        e = base_embed("🛠️ EHRP DEV CONTROL", "Server verbessern, strukturieren, sichern und automatisieren.")
        e.add_field(name="🔎 Analyse", value="`/servercheck` `/rollencheck` `/channelcheck` `/rechtecheck` `/designcheck`", inline=False)
        e.add_field(name="🧱 Struktur", value="`/channel_erstellen` `/kategorie_erstellen` `/channel_umbenennen` `/topic` `/slowmode` `/lock` `/unlock` `/channel_klonen` `/channel_loeschen`", inline=False)
        e.add_field(name="💾 Sicherheit", value="`/backup_erstellen` `/backup_liste` `/restore_missing` `/undo`", inline=False)
        e.add_field(name="📦 Vorlagen & Projekte", value="`/template_speichern` `/template_liste` `/template_bauen` `/projekt_erstellen` `/projekt_archivieren`", inline=False)
        e.add_field(name="🎙️ Voice", value="`/tempvoice_setup` `/voice_name` `/voice_limit` `/voice_lock` `/voice_unlock`", inline=False)
        e.add_field(name="👥 Team", value="`/abwesend` `/abwesenheit_ende` `/abwesenheiten` `/teamliste`", inline=False)
        e.add_field(name="🎨 Kommunikation", value="`/embed_senden` `/changelog`", inline=False)
        e.add_field(name="📊 Stats & Setup", value="`/setup` `/stats_setup` `/stats_update`", inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="ping", description="Prüft, ob der DEV-Bot reagiert.")
    async def ping(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        await interaction.response.send_message(f"✅ Online • `{round(self.bot.latency*1000)} ms`", ephemeral=True)

async def setup(bot): await bot.add_cog(Core(bot))
