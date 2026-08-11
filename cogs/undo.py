from __future__ import annotations
import json
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.db import last_action, mark_undone

class Undo(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="undo",description="Macht die letzte unterstützte DEV-Aktion rückgängig.")
    async def undo(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        row=last_action(interaction.guild_id)
        if not row:
            await interaction.response.send_message("Keine rückgängig machbare Aktion vorhanden.",ephemeral=True); return
        p=json.loads(row["payload"]); action=row["action"]
        c=interaction.guild.get_channel(p.get("channel_id",0))
        try:
            if action in {"channel_create","category_create"}:
                if c: await c.delete(reason=f"EHRP DEV UNDO • {interaction.user}")
            elif action=="channel_rename" and c:
                await c.edit(name=p["old"],reason=f"EHRP DEV UNDO • {interaction.user}")
            elif action=="topic" and isinstance(c,discord.TextChannel):
                await c.edit(topic=p.get("old"),reason=f"EHRP DEV UNDO • {interaction.user}")
            elif action=="slowmode" and isinstance(c,discord.TextChannel):
                await c.edit(slowmode_delay=int(p["old"]),reason=f"EHRP DEV UNDO • {interaction.user}")
            elif action in {"lock","unlock"} and isinstance(c,discord.TextChannel):
                role=interaction.guild.default_role; ow=c.overwrites_for(role); ow.send_messages=p.get("old")
                await c.set_permissions(role,overwrite=ow,reason=f"EHRP DEV UNDO • {interaction.user}")
            else:
                await interaction.response.send_message(f"⚠️ Letzte Aktion `{action}` kann nicht automatisch rückgängig gemacht werden.",ephemeral=True); return
            mark_undone(row["id"])
            await interaction.response.send_message(f"↩️ `{action}` wurde rückgängig gemacht.",ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Undo fehlgeschlagen: `{e}`",ephemeral=True)

async def setup(bot): await bot.add_cog(Undo(bot))
