from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.common import base_embed, truncate

POWER = ["administrator","manage_guild","manage_roles","manage_channels","ban_members","kick_members","manage_webhooks"]

class ServerScan(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="servercheck", description="Kompletter Server-Gesundheitscheck.")
    async def servercheck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        g = interaction.guild
        no_topic = [c.name for c in g.text_channels if not c.topic]
        empty_categories = [c.name for c in g.categories if not c.channels]
        duplicate_channels = []
        seen = set()
        for c in g.channels:
            key = (getattr(c.category,"id",None), c.name, str(c.type))
            if key in seen: duplicate_channels.append(c.name)
            seen.add(key)
        e = base_embed("🔎 Server Check")
        e.add_field(name="📊 Bestand", value=f"Mitglieder **{g.member_count}**\nRollen **{len(g.roles)}**\nKategorien **{len(g.categories)}**\nText **{len(g.text_channels)}**\nVoice **{len(g.voice_channels)}**", inline=False)
        e.add_field(name="⚠️ Hinweise", value=truncate(f"Ohne Topic: {', '.join(no_topic) or '—'}\nLeere Kategorien: {', '.join(empty_categories) or '—'}\nDoppelte Channels: {', '.join(duplicate_channels) or '—'}", 1000), inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="rollencheck", description="Findet Rollen mit mächtigen Rechten und Hierarchie-Probleme.")
    async def rollencheck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        rows=[]
        for r in reversed(interaction.guild.roles):
            if r.is_default() or r.managed: continue
            hits=[p.replace("_"," ") for p in POWER if getattr(r.permissions,p)]
            if hits: rows.append(f"**{r.name}** → {', '.join(hits)}")
        await interaction.response.send_message(embed=base_embed("🛡️ Rollen Check", truncate("\n".join(rows) or "✅ Keine auffälligen Rollen.")), ephemeral=True)

    @app_commands.command(name="channelcheck", description="Zeigt die Channel-Struktur.")
    async def channelcheck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        lines=[]
        for cat in interaction.guild.categories:
            lines.append(f"\n**📁 {cat.name}**")
            for c in cat.channels: lines.append(f"• {c.name}  `({c.type})`")
        await interaction.response.send_message(embed=base_embed("🗂️ Channel-Struktur", truncate("\n".join(lines))), ephemeral=True)

    @app_commands.command(name="rechtecheck", description="Prüft Bot-Rechte und wichtige Server-Berechtigungen.")
    async def rechtecheck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        me = interaction.guild.me
        p = me.guild_permissions
        needed={"manage_channels":p.manage_channels,"manage_roles":p.manage_roles,"manage_guild":p.manage_guild,"view_audit_log":p.view_audit_log,"manage_messages":p.manage_messages}
        text="\n".join(f"{'✅' if ok else '❌'} {name.replace('_',' ').title()}" for name,ok in needed.items())
        text += f"\n\nBot-Rolle: **{me.top_role.name}** • Position **{me.top_role.position}**"
        await interaction.response.send_message(embed=base_embed("🔐 Rechte Check", text), ephemeral=True)

    @app_commands.command(name="designcheck", description="Prüft optische/strukturelle Uneinheitlichkeit.")
    async def designcheck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction): return
        g=interaction.guild
        uppercase=[c.name for c in g.channels if any(x.isupper() for x in c.name)]
        spaces=[c.name for c in g.text_channels if " " in c.name]
        no_topic=[c.name for c in g.text_channels if not c.topic]
        text=f"Channels mit Großbuchstaben: **{len(uppercase)}**\nTextchannels mit Leerzeichen: **{len(spaces)}**\nTextchannels ohne Topic: **{len(no_topic)}**\n\n💡 Der Bot ändert Design nie ungefragt; er zeigt nur Auffälligkeiten."
        await interaction.response.send_message(embed=base_embed("✨ Design Check", text), ephemeral=True)

async def setup(bot): await bot.add_cog(ServerScan(bot))
