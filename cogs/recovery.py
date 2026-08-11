from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import BACKUP_DIR
from utils.checks import ensure_dev


RECOVERY_DIR = Path(BACKUP_DIR) / "recovery"
RECOVERY_DIR.mkdir(parents=True, exist_ok=True)

RECOVERY_PLAN = {}

REASONS = (
    "redesign",
    "rollback",
    "ehrp server redesign",
    "ehrp redesign",
)


def is_recovery_related(entry: discord.AuditLogEntry) -> bool:
    reason = (entry.reason or "").lower()
    return any(x in reason for x in REASONS)


async def collect_entries(guild: discord.Guild, bot_id: int):
    entries = []

    async for entry in guild.audit_logs(
        limit=None,
        user=discord.Object(id=bot_id),
    ):
        if entry.user is None or entry.user.id != bot_id:
            continue

        if entry.action not in (
            discord.AuditLogAction.channel_update,
            discord.AuditLogAction.role_update,
        ):
            continue

        if not is_recovery_related(entry):
            continue

        entries.append(entry)

    return entries


def get_attr(diff, name):
    if hasattr(diff, name):
        return getattr(diff, name)
    return None


def build_original_plan(entries):
    """
    Wir wollen den ALLERERSTEN Zustand vor der kompletten Serie.

    Discord Audit Log kommt newest -> oldest.
    Wir sortieren oldest -> newest und merken uns pro Objekt
    den ersten bekannten BEFORE-Wert jedes Feldes.
    """
    ordered = sorted(entries, key=lambda e: e.created_at)

    objects = {}

    for entry in ordered:
        target = entry.target

        if target is None:
            continue

        target_id = target.id

        if target_id not in objects:
            objects[target_id] = {
                "id": target_id,
                "type": (
                    "role"
                    if entry.action == discord.AuditLogAction.role_update
                    else "channel"
                ),
                "fields": {},
                "first_seen": entry.created_at.isoformat(),
            }

        item = objects[target_id]
        before = entry.before

        supported = (
            "name",
            "topic",
            "position",
            "category",
            "slowmode_delay",
            "nsfw",
            "user_limit",
            "bitrate",
            "colour",
            "hoist",
            "mentionable",
            "permissions",
        )

        for field in supported:
            if field in item["fields"]:
                continue

            if hasattr(before, field):
                value = getattr(before, field)

                if field == "category":
                    item["fields"][field] = (
                        value.id if value is not None else None
                    )
                elif field == "colour":
                    item["fields"][field] = (
                        value.value if value is not None else None
                    )
                elif field == "permissions":
                    item["fields"][field] = (
                        value.value if value is not None else None
                    )
                else:
                    item["fields"][field] = value

    return objects


def save_current_state(guild: discord.Guild) -> Path:
    data = {
        "guild_id": guild.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "channels": [],
        "roles": [],
    }

    for ch in guild.channels:
        item = {
            "id": ch.id,
            "name": ch.name,
            "position": ch.position,
            "category_id": getattr(ch, "category_id", None),
            "type": str(ch.type),
        }

        if isinstance(ch, discord.TextChannel):
            item.update({
                "topic": ch.topic,
                "slowmode_delay": ch.slowmode_delay,
                "nsfw": ch.nsfw,
            })

        if isinstance(ch, discord.VoiceChannel):
            item.update({
                "user_limit": ch.user_limit,
                "bitrate": ch.bitrate,
            })

        data["channels"].append(item)

    for role in guild.roles:
        if role.is_default():
            continue

        data["roles"].append({
            "id": role.id,
            "name": role.name,
            "position": role.position,
            "colour": role.colour.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "permissions": role.permissions.value,
        })

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = RECOVERY_DIR / f"before_full_recovery_{guild.id}_{stamp}.json"

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path


async def restore_channel(guild, item):
    ch = guild.get_channel(item["id"])

    if ch is None:
        return False, "Channel existiert nicht mehr"

    fields = item["fields"]
    kwargs = {}

    if "name" in fields:
        kwargs["name"] = fields["name"]

    if isinstance(ch, discord.TextChannel):
        if "topic" in fields:
            kwargs["topic"] = fields["topic"]

        if "slowmode_delay" in fields:
            kwargs["slowmode_delay"] = fields["slowmode_delay"]

        if "nsfw" in fields:
            kwargs["nsfw"] = fields["nsfw"]

    if isinstance(ch, discord.VoiceChannel):
        if "user_limit" in fields:
            kwargs["user_limit"] = fields["user_limit"]

        if "bitrate" in fields:
            kwargs["bitrate"] = fields["bitrate"]

    if "category" in fields:
        category_id = fields["category"]

        kwargs["category"] = (
            guild.get_channel(category_id)
            if category_id is not None
            else None
        )

    try:
        if kwargs:
            await ch.edit(
                **kwargs,
                reason="EHRP FULL RECOVERY",
            )

        if "position" in fields:
            await ch.edit(
                position=fields["position"],
                reason="EHRP FULL RECOVERY",
            )

        return True, None

    except discord.Forbidden:
        return False, "Fehlende Berechtigung"

    except discord.HTTPException as e:
        return False, str(e)


async def restore_role(guild, item):
    role = guild.get_role(item["id"])

    if role is None:
        return False, "Rolle existiert nicht mehr"

    if role.managed:
        return False, "Managed-Rolle"

    fields = item["fields"]
    kwargs = {}

    if "name" in fields:
        kwargs["name"] = fields["name"]

    if "colour" in fields:
        kwargs["colour"] = discord.Colour(fields["colour"])

    if "hoist" in fields:
        kwargs["hoist"] = fields["hoist"]

    if "mentionable" in fields:
        kwargs["mentionable"] = fields["mentionable"]

    if "permissions" in fields:
        kwargs["permissions"] = discord.Permissions(
            fields["permissions"]
        )

    try:
        if kwargs:
            await role.edit(
                **kwargs,
                reason="EHRP FULL RECOVERY",
            )

        if "position" in fields:
            await guild.edit_role_positions(
                positions={
                    role: fields["position"]
                },
                reason="EHRP FULL RECOVERY",
            )

        return True, None

    except discord.Forbidden:
        return False, "Fehlende Berechtigung"

    except discord.HTTPException as e:
        return False, str(e)


async def execute_recovery(guild, plan):
    restored = 0
    failed = []

    for item in plan.values():
        if item["type"] == "channel":
            ok, error = await restore_channel(guild, item)
        else:
            ok, error = await restore_role(guild, item)

        if ok:
            restored += 1
        else:
            failed.append({
                "id": item["id"],
                "error": error,
            })

    return restored, failed


def preview_text(plan, entries):
    channel_count = sum(
        1 for x in plan.values()
        if x["type"] == "channel"
    )

    role_count = sum(
        1 for x in plan.values()
        if x["type"] == "role"
    )

    lines = [
        "🛡️ **FULL RECOVERY BEREIT**",
        "",
        f"Audit-Einträge analysiert: **{len(entries)}**",
        f"Eindeutige Objekte: **{len(plan)}**",
        f"📁 Channels/Kategorien: **{channel_count}**",
        f"🎭 Rollen: **{role_count}**",
        "",
        "Der Bot wird NICHT alle 656 Schritte einzeln zurückspielen.",
        "Er setzt jedes Objekt direkt auf den frühesten bekannten Zustand zurück.",
        "",
        "💾 Vorher wird der jetzige Zustand zusätzlich gespeichert.",
        "",
        "⚠️ Gelöschte Channels/Nachrichten können damit nicht wiederhergestellt werden.",
    ]

    return "\n".join(lines)


class RecoveryConfirm(discord.ui.View):
    def __init__(self, owner_id, guild_id):
        super().__init__(timeout=600)

        self.owner_id = owner_id
        self.guild_id = guild_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Nur der Developer darf das starten.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="ALLES WIEDERHERSTELLEN",
        emoji="🛡️",
        style=discord.ButtonStyle.danger,
    )
    async def recover(self, interaction, button):
        data = RECOVERY_PLAN.get(self.guild_id)

        if not data:
            await interaction.response.send_message(
                "❌ Recovery-Plan nicht mehr vorhanden. "
                "Bitte `/full_recovery_scan` erneut ausführen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        save_current_state(interaction.guild)

        restored, failed = await execute_recovery(
            interaction.guild,
            data["plan"],
        )

        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        text = (
            "🛡️ **FULL RECOVERY BEENDET**\n\n"
            f"✅ Wiederhergestellt: **{restored} Objekte**\n"
            f"⚠️ Fehler: **{len(failed)}**"
        )

        await interaction.followup.send(
            text,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Abbrechen",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(self, interaction, button):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="❌ Recovery abgebrochen. Es wurde nichts verändert.",
            view=self,
        )


class Recovery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="full_recovery_scan",
        description="Berechnet den ursprünglichen Zustand vor dem DEV-Redesign.",
    )
    async def full_recovery_scan(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        me = guild.me

        if me is None or not me.guild_permissions.view_audit_log:
            await interaction.response.send_message(
                "❌ Mir fehlt Audit-Log anzeigen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        entries = await collect_entries(
            guild,
            self.bot.user.id,
        )

        if not entries:
            await interaction.followup.send(
                "❌ Keine passenden Änderungen gefunden.",
                ephemeral=True,
            )
            return

        plan = build_original_plan(entries)

        RECOVERY_PLAN[guild.id] = {
            "plan": plan,
            "entries": entries,
        }

        await interaction.followup.send(
            preview_text(plan, entries),
            view=RecoveryConfirm(
                interaction.user.id,
                guild.id,
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Recovery(bot))
