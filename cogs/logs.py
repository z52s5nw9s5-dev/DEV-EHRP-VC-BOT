from __future__ import annotations
import discord
from discord.ext import commands
from utils.logging import send_log

class Logs(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self,channel):
        await send_log(channel.guild,"➕ Channel erstellt",f"**{channel.name}** (`{channel.id}`)")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self,channel):
        await send_log(channel.guild,"🗑️ Channel gelöscht",f"**{channel.name}** (`{channel.id}`)")

    @commands.Cog.listener()
    async def on_guild_channel_update(self,before,after):
        changes=[]
        if before.name!=after.name: changes.append(f"Name: **{before.name}** → **{after.name}**")
        if isinstance(before,discord.TextChannel) and isinstance(after,discord.TextChannel):
            if before.topic!=after.topic: changes.append("Topic geändert")
            if before.slowmode_delay!=after.slowmode_delay: changes.append(f"Slowmode: {before.slowmode_delay}s → {after.slowmode_delay}s")
        if changes: await send_log(after.guild,"✏️ Channel geändert","\n".join(changes))

    @commands.Cog.listener()
    async def on_guild_role_create(self,role): await send_log(role.guild,"➕ Rolle erstellt",f"**{role.name}**")

    @commands.Cog.listener()
    async def on_guild_role_delete(self,role): await send_log(role.guild,"🗑️ Rolle gelöscht",f"**{role.name}**")

    @commands.Cog.listener()
    async def on_guild_role_update(self,before,after):
        changes=[]
        if before.name!=after.name: changes.append(f"Name: **{before.name}** → **{after.name}**")
        if before.permissions!=after.permissions: changes.append("Berechtigungen geändert")
        if changes: await send_log(after.guild,"🛡️ Rolle geändert","\n".join(changes))

    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if before.roles!=after.roles:
            b={r.id:r for r in before.roles}; a={r.id:r for r in after.roles}
            added=[r.name for i,r in a.items() if i not in b]; removed=[r.name for i,r in b.items() if i not in a]
            text=f"Mitglied: {after.mention}\n"
            if added: text+=f"➕ {', '.join(added)}\n"
            if removed: text+=f"➖ {', '.join(removed)}"
            await send_log(after.guild,"👤 Rollen geändert",text)

async def setup(bot): await bot.add_cog(Logs(bot))
