from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import ensure_dev
from utils.db import set_setting,get_setting,save_temp_voice,get_temp_voice,delete_temp_voice

class Voice(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="tempvoice_setup",description="Erstellt/setzt den 'Join to Create'-Voicechannel.")
    async def setup_voice(self,interaction:discord.Interaction,kategorie:discord.CategoryChannel):
        if not await ensure_dev(interaction): return
        lobby=await interaction.guild.create_voice_channel("➕・Raum erstellen",category=kategorie,reason="EHRP DEV tempvoice")
        set_setting(interaction.guild_id,"tempvoice_lobby_id",lobby.id)
        await interaction.response.send_message(f"✅ TempVoice aktiv: {lobby.mention}",ephemeral=True)

    async def _owned_channel(self,interaction):
        if not isinstance(interaction.user,discord.Member) or not interaction.user.voice: return None
        c=interaction.user.voice.channel; row=get_temp_voice(c.id)
        return c if row and row["owner_id"]==interaction.user.id else None

    @app_commands.command(name="voice_name",description="Benennt deinen temporären Voice-Raum um.")
    async def voice_name(self,interaction:discord.Interaction,name:str):
        c=await self._owned_channel(interaction)
        if not c: await interaction.response.send_message("❌ Du bist nicht Owner eines TempVoice-Raums.",ephemeral=True); return
        await c.edit(name=name); await interaction.response.send_message("✅ Umbenannt.",ephemeral=True)

    @app_commands.command(name="voice_limit",description="Setzt das User-Limit deines TempVoice-Raums.")
    async def voice_limit(self,interaction:discord.Interaction,limit:app_commands.Range[int,0,99]):
        c=await self._owned_channel(interaction)
        if not c: await interaction.response.send_message("❌ Kein eigener TempVoice-Raum.",ephemeral=True); return
        await c.edit(user_limit=limit); await interaction.response.send_message(f"✅ Limit: **{limit or '∞'}**",ephemeral=True)

    @app_commands.command(name="voice_lock",description="Sperrt deinen TempVoice-Raum.")
    async def voice_lock(self,interaction:discord.Interaction):
        c=await self._owned_channel(interaction)
        if not c: await interaction.response.send_message("❌ Kein eigener TempVoice-Raum.",ephemeral=True); return
        ow=c.overwrites_for(interaction.guild.default_role); ow.connect=False
        await c.set_permissions(interaction.guild.default_role,overwrite=ow); await interaction.response.send_message("🔒 Gesperrt.",ephemeral=True)

    @app_commands.command(name="voice_unlock",description="Entsperrt deinen TempVoice-Raum.")
    async def voice_unlock(self,interaction:discord.Interaction):
        c=await self._owned_channel(interaction)
        if not c: await interaction.response.send_message("❌ Kein eigener TempVoice-Raum.",ephemeral=True); return
        ow=c.overwrites_for(interaction.guild.default_role); ow.connect=None
        await c.set_permissions(interaction.guild.default_role,overwrite=ow); await interaction.response.send_message("🔓 Entsperrt.",ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self,member:discord.Member,before:discord.VoiceState,after:discord.VoiceState):
        lobby_raw=get_setting(member.guild.id,"tempvoice_lobby_id")
        if after.channel and lobby_raw and after.channel.id==int(lobby_raw):
            c=await member.guild.create_voice_channel(f"🔊・{member.display_name}",category=after.channel.category,reason="EHRP DEV tempvoice")
            ow=c.overwrites_for(member); ow.manage_channels=True; ow.move_members=True; ow.connect=True
            await c.set_permissions(member,overwrite=ow)
            save_temp_voice(c.id,member.guild.id,member.id)
            try: await member.move_to(c)
            except discord.HTTPException: pass
        if before.channel:
            row=get_temp_voice(before.channel.id)
            if row and len(before.channel.members)==0:
                delete_temp_voice(before.channel.id)
                try: await before.channel.delete(reason="EHRP DEV empty tempvoice")
                except discord.HTTPException: pass

async def setup(bot): await bot.add_cog(Voice(bot))
