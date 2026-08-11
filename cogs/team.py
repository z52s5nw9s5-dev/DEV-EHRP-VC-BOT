from __future__ import annotations
from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands
from config import DEV_ROLE_ID
from utils.checks import ensure_dev
from utils.db import add_absence,end_absence,active_absences
from utils.common import base_embed,truncate

class Team(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="abwesend",description="Trägt eine Team-Abwesenheit ein.")
    async def absent(self,interaction:discord.Interaction,tage:app_commands.Range[int,1,365],grund:str="Kein Grund angegeben"):
        if not await ensure_dev(interaction): return
        until=datetime.now(timezone.utc)+timedelta(days=tage)
        add_absence(interaction.guild_id,interaction.user.id,grund,until.isoformat())
        await interaction.response.send_message(f"✅ Abwesend bis <t:{int(until.timestamp())}:D> eingetragen.",ephemeral=True)

    @app_commands.command(name="abwesenheit_ende",description="Beendet deine aktive Abwesenheit.")
    async def end(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        ok=end_absence(interaction.guild_id,interaction.user.id)
        await interaction.response.send_message("✅ Abwesenheit beendet." if ok else "Keine aktive Abwesenheit.",ephemeral=True)

    @app_commands.command(name="abwesenheiten",description="Zeigt aktive Team-Abwesenheiten.")
    async def list_(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        rows=active_absences(interaction.guild_id); lines=[]
        for r in rows:
            m=interaction.guild.get_member(r["user_id"]); name=m.mention if m else str(r["user_id"])
            until=f" • bis `{r['until_at'][:10]}`" if r["until_at"] else ""
            lines.append(f"{name}{until} — {r['reason']}")
        await interaction.response.send_message(embed=base_embed("🏖️ Abwesenheiten",truncate("\n".join(lines) or "Keine aktiven Abwesenheiten.")),ephemeral=True)

    @app_commands.command(name="teamliste",description="Zeigt Mitglieder mit der DEV-Rolle.")
    async def teamlist(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        role=interaction.guild.get_role(DEV_ROLE_ID)
        members=role.members if role else []
        text="\n".join(f"• {m.mention} — `{m.display_name}`" for m in members) or "Keine Mitglieder gefunden."
        await interaction.response.send_message(embed=base_embed("👥 DEV-Team",truncate(text)),ephemeral=True)

async def setup(bot): await bot.add_cog(Team(bot))
