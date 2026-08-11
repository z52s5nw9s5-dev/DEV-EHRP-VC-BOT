from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands
from config import BACKUP_DIR
from utils.checks import ensure_dev
from utils.common import base_embed
from utils.confirm import ConfirmView
from utils.db import get_setting

BACKUPS=Path(BACKUP_DIR); BACKUPS.mkdir(parents=True,exist_ok=True)

def perms_to_dict(ow: discord.PermissionOverwrite):
    allow,deny=ow.pair(); return {"allow":allow.value,"deny":deny.value}

def serialize_overwrites(channel):
    out=[]
    for target,ow in channel.overwrites.items():
        out.append({"target_id":target.id,"target_type":"role" if isinstance(target,discord.Role) else "member",**perms_to_dict(ow)})
    return out

def make_overwrites(guild, data):
    out={}
    for item in data:
        target=guild.get_role(item["target_id"]) if item["target_type"]=="role" else guild.get_member(item["target_id"])
        if not target: continue
        out[target]=discord.PermissionOverwrite.from_pair(discord.Permissions(item["allow"]),discord.Permissions(item["deny"]))
    return out

def build_backup(guild):
    roles=[]
    for r in guild.roles:
        if r.is_default(): continue
        roles.append({"id":r.id,"name":r.name,"position":r.position,"permissions":r.permissions.value,"colour":r.colour.value,"hoist":r.hoist,"mentionable":r.mentionable,"managed":r.managed})
    cats=[]
    for cat in guild.categories:
        cd={"id":cat.id,"name":cat.name,"position":cat.position,"overwrites":serialize_overwrites(cat),"channels":[]}
        for c in cat.channels:
            d={"id":c.id,"name":c.name,"position":c.position,"type":str(c.type),"overwrites":serialize_overwrites(c)}
            if isinstance(c,discord.TextChannel): d.update(topic=c.topic,slowmode_delay=c.slowmode_delay,nsfw=c.nsfw)
            if isinstance(c,discord.VoiceChannel): d.update(bitrate=c.bitrate,user_limit=c.user_limit)
            cd["channels"].append(d)
        cats.append(cd)
    unc=[]
    for c in guild.channels:
        if isinstance(c,discord.CategoryChannel) or c.category: continue
        d={"id":c.id,"name":c.name,"position":c.position,"type":str(c.type),"overwrites":serialize_overwrites(c)}
        if isinstance(c,discord.TextChannel): d.update(topic=c.topic,slowmode_delay=c.slowmode_delay,nsfw=c.nsfw)
        if isinstance(c,discord.VoiceChannel): d.update(bitrate=c.bitrate,user_limit=c.user_limit)
        unc.append(d)
    return {"version":2,"guild":{"id":guild.id,"name":guild.name},"created_at":datetime.now(timezone.utc).isoformat(),"roles":roles,"categories":cats,"uncategorized":unc}

class Backup(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="backup_erstellen",description="Vollbackup von Rollen, Channels und Overwrites.")
    async def create(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        await interaction.response.defer(ephemeral=True)
        data=build_backup(interaction.guild); stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path=BACKUPS/f"ehrp_full_{stamp}.json"; path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        raw=get_setting(interaction.guild_id,"backup_channel_id")
        if raw:
            ch=interaction.guild.get_channel(int(raw))
            if isinstance(ch,discord.TextChannel):
                try: await ch.send(content=f"💾 Backup von {interaction.user.mention}",file=discord.File(path))
                except discord.HTTPException: pass
        await interaction.followup.send(embed=base_embed("💾 Vollbackup erstellt",f"`{path.name}`\nRollen: **{len(data['roles'])}**\nKategorien: **{len(data['categories'])}**"),ephemeral=True)

    @app_commands.command(name="backup_liste",description="Zeigt die letzten lokalen Backups.")
    async def list_(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        arr=sorted(BACKUPS.glob("*.json"),reverse=True)[:15]
        await interaction.response.send_message(embed=base_embed("💾 Backups","\n".join(f"• `{p.name}`" for p in arr) or "Keine Backups."),ephemeral=True)

    @app_commands.command(name="restore_missing",description="Stellt fehlende Rollen/Kategorien/Channels aus dem neuesten Backup wieder her, ohne Bestehendes zu löschen.")
    async def restore_missing(self,interaction:discord.Interaction):
        if not await ensure_dev(interaction): return
        arr=sorted(BACKUPS.glob("*.json"),reverse=True)
        if not arr:
            await interaction.response.send_message("❌ Kein Backup vorhanden.",ephemeral=True); return
        view=ConfirmView(interaction.user.id)
        await interaction.response.send_message(f"⚠️ Fehlende Struktur aus `{arr[0].name}` ergänzen? Bestehende Channels werden **nicht gelöscht**.",view=view,ephemeral=True)
        await view.wait()
        if view.value is not True: return
        data=json.loads(arr[0].read_text(encoding="utf-8")); g=interaction.guild; made=[]
        role_by_old={}
        by_name={r.name:r for r in g.roles}
        for rd in sorted(data["roles"],key=lambda x:x["position"]):
            if rd.get("managed"): continue
            r=by_name.get(rd["name"])
            if not r:
                try:
                    r=await g.create_role(name=rd["name"],permissions=discord.Permissions(rd["permissions"]),colour=discord.Colour(rd["colour"]),hoist=rd["hoist"],mentionable=rd["mentionable"],reason="EHRP DEV restore")
                    made.append(f"Rolle {r.name}")
                except discord.HTTPException: continue
            role_by_old[rd["id"]]=r
        cats_by_name={c.name:c for c in g.categories}
        for cd in data["categories"]:
            cat=cats_by_name.get(cd["name"])
            if not cat:
                cat=await g.create_category(cd["name"],reason="EHRP DEV restore"); made.append(f"Kategorie {cat.name}")
            existing={(c.name,str(c.type)) for c in cat.channels}
            for d in cd["channels"]:
                key=(d["name"],d["type"])
                if key in existing: continue
                try:
                    if d["type"]=="text":
                        c=await g.create_text_channel(d["name"],category=cat,topic=d.get("topic"),slowmode_delay=d.get("slowmode_delay",0),nsfw=d.get("nsfw",False),reason="EHRP DEV restore")
                    elif d["type"]=="voice":
                        c=await g.create_voice_channel(d["name"],category=cat,user_limit=d.get("user_limit",0),reason="EHRP DEV restore")
                    else: continue
                    made.append(f"Channel {c.name}")
                except discord.HTTPException: pass
        await interaction.followup.send("✅ Restore abgeschlossen.\n"+("\n".join(made[:30]) if made else "Es fehlte nichts."),ephemeral=True)

async def setup(bot): await bot.add_cog(Backup(bot))
