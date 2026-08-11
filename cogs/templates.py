from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.db import save_template,get_template,list_templates,delete_template
from utils.common import base_embed

class Templates(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="template_speichern",description="Speichert eine Kategorie als wiederverwendbare Vorlage.")
    async def save(self,interaction:discord.Interaction,kategorie:discord.CategoryChannel,name:str):
        if not await ensure_dev(interaction): return
        channels=[]
        for c in kategorie.channels:
            if isinstance(c,discord.TextChannel): channels.append({"type":"text","name":c.name,"topic":c.topic,"slowmode":c.slowmode_delay})
            elif isinstance(c,discord.VoiceChannel): channels.append({"type":"voice","name":c.name,"limit":c.user_limit})
        save_template(interaction.guild_id,name,{"category":kategorie.name,"channels":channels},interaction.user.id)
        await interaction.response.send_message(f"✅ Template **{name}** gespeichert ({len(channels)} Channels).",ephemeral=True)

    @app_commands.command(name="template_liste",description="Zeigt gespeicherte Templates.")
    async def list_(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        names=list_templates(interaction.guild_id)
        await interaction.response.send_message(embed=base_embed("📦 Templates","\n".join(f"• `{x}`" for x in names) or "Keine Templates."),ephemeral=True)

    @app_commands.command(name="template_bauen",description="Erstellt einen Bereich aus einem Template.")
    async def build(self,interaction:discord.Interaction,name:str,kategorie_name:str|None=None):
        if not await ensure_dev(interaction): return
        t=get_template(interaction.guild_id,name)
        if not t:
            await interaction.response.send_message("❌ Template nicht gefunden.",ephemeral=True); return
        cat=await interaction.guild.create_category(kategorie_name or t["category"],reason=f"Template {name}")
        for d in t["channels"]:
            if d["type"]=="text": await interaction.guild.create_text_channel(d["name"],category=cat,topic=d.get("topic"),slowmode_delay=d.get("slowmode",0))
            elif d["type"]=="voice": await interaction.guild.create_voice_channel(d["name"],category=cat,user_limit=d.get("limit",0))
        await interaction.response.send_message(f"✅ Template **{name}** als **{cat.name}** gebaut.",ephemeral=True)

    @app_commands.command(name="template_loeschen",description="Löscht eine gespeicherte Vorlage.")
    async def delete(self,interaction:discord.Interaction,name:str):
        if not await ensure_dev(interaction): return
        ok=delete_template(interaction.guild_id,name)
        await interaction.response.send_message("✅ Gelöscht." if ok else "❌ Nicht gefunden.",ephemeral=True)

async def setup(bot): await bot.add_cog(Templates(bot))
