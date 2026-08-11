from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.checks import ensure_dev
from utils.db import set_setting,get_setting

class Stats(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.stats_loop.start()

    def cog_unload(self): self.stats_loop.cancel()

    async def _update(self,guild:discord.Guild):
        pairs=[("stats_members_id",f"👥・Mitglieder: {guild.member_count}"),
               ("stats_bots_id",f"🤖・Bots: {sum(1 for m in guild.members if m.bot)}"),
               ("stats_team_id",f"🛠️・DEV: {sum(1 for m in guild.members if any(r.name.lower().find('dev')>=0 for r in m.roles))}")]
        for key,name in pairs:
            raw=get_setting(guild.id,key)
            if raw:
                c=guild.get_channel(int(raw))
                if isinstance(c,discord.VoiceChannel) and c.name!=name:
                    try: await c.edit(name=name,reason="EHRP DEV stats")
                    except discord.HTTPException: pass

    @app_commands.command(name="stats_setup",description="Erstellt automatische Server-Statistik-Channels.")
    async def setup_stats(self,interaction:discord.Interaction,kategorie:discord.CategoryChannel|None=None):
        if not await ensure_dev(interaction): return
        g=interaction.guild
        c1=await g.create_voice_channel(f"👥・Mitglieder: {g.member_count}",category=kategorie)
        c2=await g.create_voice_channel(f"🤖・Bots: {sum(1 for m in g.members if m.bot)}",category=kategorie)
        c3=await g.create_voice_channel("🛠️・DEV: 0",category=kategorie)
        for c in (c1,c2,c3):
            ow=c.overwrites_for(g.default_role); ow.connect=False; await c.set_permissions(g.default_role,overwrite=ow)
        set_setting(g.id,"stats_members_id",c1.id); set_setting(g.id,"stats_bots_id",c2.id); set_setting(g.id,"stats_team_id",c3.id)
        await self._update(g)
        await interaction.response.send_message("✅ Server-Stats erstellt und Auto-Update aktiviert.",ephemeral=True)

    @app_commands.command(name="stats_update",description="Aktualisiert Server-Statistiken sofort.")
    async def update_stats(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        await self._update(interaction.guild); await interaction.response.send_message("✅ Stats aktualisiert.",ephemeral=True)

    @tasks.loop(minutes=15)
    async def stats_loop(self):
        for g in self.bot.guilds: await self._update(g)

    @stats_loop.before_loop
    async def before_stats(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(Stats(bot))
