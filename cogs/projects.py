from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.db import get_setting
from utils.confirm import ConfirmView

class Projects(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="projekt_erstellen",description="Erstellt einen kompletten Projekt-/Event-Bereich.")
    async def create(self,interaction:discord.Interaction,name:str,mit_voice:bool=True):
        if not await ensure_dev(interaction): return
        g=interaction.guild
        cat=await g.create_category(f"📁 {name}",reason=f"EHRP DEV Projekt • {interaction.user}")
        await g.create_text_channel("📌・info",category=cat,topic=f"Informationen zu {name}")
        await g.create_text_channel("💬・chat",category=cat,topic=f"Interner Chat für {name}")
        await g.create_text_channel("📝・planung",category=cat,topic=f"Planung und Aufgaben für {name}")
        if mit_voice: await g.create_voice_channel("🔊・besprechung",category=cat)
        await interaction.response.send_message(f"✅ Projektbereich **{cat.name}** erstellt.",ephemeral=True)

    @app_commands.command(name="projekt_archivieren",description="Verschiebt eine Kategorie ins Archiv und sperrt Textchannels.")
    async def archive(self,interaction:discord.Interaction,kategorie:discord.CategoryChannel):
        if not await ensure_dev(interaction): return
        raw=get_setting(interaction.guild_id,"archive_category_id")
        view=ConfirmView(interaction.user.id)
        await interaction.response.send_message(f"⚠️ **{kategorie.name}** archivieren?",view=view,ephemeral=True)
        await view.wait()
        if view.value is not True: return
        for c in kategorie.channels:
            if isinstance(c,discord.TextChannel):
                ow=c.overwrites_for(interaction.guild.default_role); ow.send_messages=False
                await c.set_permissions(interaction.guild.default_role,overwrite=ow,reason="EHRP DEV archive")
        await kategorie.edit(name=f"🗃️ {kategorie.name.removeprefix('🗃️ ')}",reason="EHRP DEV archive")
        note=""
        if raw:
            archive_cat=interaction.guild.get_channel(int(raw))
            if isinstance(archive_cat,discord.CategoryChannel): note=f"\nArchiv-Sammelkategorie ist **{archive_cat.name}**; Discord erlaubt Kategorien jedoch nicht in Kategorien zu verschieben."
        await interaction.followup.send(f"✅ Projekt archiviert.{note}",ephemeral=True)

async def setup(bot): await bot.add_cog(Projects(bot))
