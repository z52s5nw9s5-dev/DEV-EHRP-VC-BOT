from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.confirm import ConfirmView
from utils.db import record_action
from utils.logging import send_log

class ServerTools(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="kategorie_erstellen", description="Erstellt eine Kategorie.")
    async def category_create(self, interaction: discord.Interaction, name: str):
        if not await ensure_dev(interaction): return
        c=await interaction.guild.create_category(name=name, reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id, interaction.user.id, "category_create", {"channel_id":c.id})
        await send_log(interaction.guild,"📁 Kategorie erstellt",f"**{c.name}** von {interaction.user.mention}")
        await interaction.response.send_message(f"✅ Kategorie **{c.name}** erstellt.",ephemeral=True)

    @app_commands.command(name="channel_erstellen", description="Erstellt Text- oder Voice-Channel.")
    @app_commands.choices(typ=[app_commands.Choice(name="Text",value="text"),app_commands.Choice(name="Voice",value="voice")])
    async def channel_create(self, interaction: discord.Interaction, name:str, typ:app_commands.Choice[str], kategorie:discord.CategoryChannel|None=None):
        if not await ensure_dev(interaction): return
        if typ.value=="text": c=await interaction.guild.create_text_channel(name,category=kategorie,reason=f"EHRP DEV • {interaction.user}")
        else: c=await interaction.guild.create_voice_channel(name,category=kategorie,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"channel_create",{"channel_id":c.id})
        await send_log(interaction.guild,"➕ Channel erstellt",f"{c.mention} von {interaction.user.mention}")
        await interaction.response.send_message(f"✅ {c.mention} erstellt.",ephemeral=True)

    @app_commands.command(name="channel_umbenennen", description="Benennt einen Channel um.")
    async def rename(self, interaction:discord.Interaction, channel:discord.TextChannel, neuer_name:str):
        if not await ensure_dev(interaction): return
        old=channel.name
        await channel.edit(name=neuer_name,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"channel_rename",{"channel_id":channel.id,"old":old,"new":neuer_name})
        await interaction.response.send_message(f"✅ **{old}** → **{neuer_name}**",ephemeral=True)

    @app_commands.command(name="topic", description="Setzt die Beschreibung eines Textchannels.")
    async def topic(self, interaction:discord.Interaction, channel:discord.TextChannel, text:str):
        if not await ensure_dev(interaction): return
        old=channel.topic
        await channel.edit(topic=text,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"topic",{"channel_id":channel.id,"old":old,"new":text})
        await interaction.response.send_message(f"✅ Topic von {channel.mention} aktualisiert.",ephemeral=True)

    @app_commands.command(name="slowmode", description="Setzt Slowmode in Sekunden (0 = aus).")
    async def slowmode(self, interaction:discord.Interaction, channel:discord.TextChannel, sekunden:app_commands.Range[int,0,21600]):
        if not await ensure_dev(interaction): return
        old=channel.slowmode_delay
        await channel.edit(slowmode_delay=sekunden,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"slowmode",{"channel_id":channel.id,"old":old,"new":sekunden})
        await interaction.response.send_message(f"✅ Slowmode: **{sekunden}s**",ephemeral=True)

    @app_commands.command(name="lock", description="Sperrt Senden für @everyone im Textchannel.")
    async def lock(self, interaction:discord.Interaction, channel:discord.TextChannel):
        if not await ensure_dev(interaction): return
        role=interaction.guild.default_role
        old=channel.overwrites_for(role).send_messages
        ow=channel.overwrites_for(role); ow.send_messages=False
        await channel.set_permissions(role,overwrite=ow,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"lock",{"channel_id":channel.id,"old":old})
        await interaction.response.send_message(f"🔒 {channel.mention} gesperrt.",ephemeral=True)

    @app_commands.command(name="unlock", description="Entsperrt Senden für @everyone.")
    async def unlock(self, interaction:discord.Interaction, channel:discord.TextChannel):
        if not await ensure_dev(interaction): return
        role=interaction.guild.default_role
        old=channel.overwrites_for(role).send_messages
        ow=channel.overwrites_for(role); ow.send_messages=None
        await channel.set_permissions(role,overwrite=ow,reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"unlock",{"channel_id":channel.id,"old":old})
        await interaction.response.send_message(f"🔓 {channel.mention} entsperrt.",ephemeral=True)

    @app_commands.command(name="channel_klonen", description="Klont einen Channel inklusive Basis-Einstellungen.")
    async def clone(self, interaction:discord.Interaction, channel:discord.TextChannel, neuer_name:str|None=None):
        if not await ensure_dev(interaction): return
        c=await channel.clone(name=neuer_name or f"{channel.name}-copy",reason=f"EHRP DEV • {interaction.user}")
        record_action(interaction.guild_id,interaction.user.id,"channel_create",{"channel_id":c.id})
        await interaction.response.send_message(f"✅ Klon erstellt: {c.mention}",ephemeral=True)

    @app_commands.command(name="channel_loeschen", description="Löscht einen Channel nach Bestätigung.")
    async def delete(self, interaction:discord.Interaction, channel:discord.TextChannel):
        if not await ensure_dev(interaction): return
        view=ConfirmView(interaction.user.id)
        await interaction.response.send_message(f"⚠️ **{channel.name}** wirklich löschen? Vorher am besten `/backup_erstellen`.",view=view,ephemeral=True)
        await view.wait()
        if view.value is not True: return
        name=channel.name
        await channel.delete(reason=f"EHRP DEV • {interaction.user}")
        await send_log(interaction.guild,"🗑️ Channel gelöscht",f"**{name}** von {interaction.user.mention}")

async def setup(bot): await bot.add_cog(ServerTools(bot))
