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

# Speichert den letzten Scan nur im laufenden Prozess.
RECOVERY_SCANS: dict[int, dict] = {}

# Nur diese Gründe gehören zu unserem kaputten Redesign-Vorgang.
BAD_REASON_WORDS = (
    "redesign",
    "design rollback",
    "server redesign",
    "ehrp redesign",
)

# Bei einer großen Serie dürfen kleine Zeitabstände zwischen Audit-Einträgen liegen.
MAX_GAP_SECONDS = 180


def reason_is_redesign(reason: str | None) -> bool:
    if not reason:
        return False

    low = reason.lower()
    return any(word in low for word in BAD_REASON_WORDS)


def safe_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except (AttributeError, TypeError):
        return default


def changed_fields(entry: discord.AuditLogEntry) -> list[str]:
    fields = []

    before = entry.before
    after = entry.after

    candidates = (
        "name",
        "topic",
        "position",
        "category",
        "slowmode_delay",
        "nsfw",
        "user_limit",
        "bitrate",
        "permissions",
        "colour",
        "hoist",
        "mentionable",
    )

    for field in candidates:
        b = safe_attr(before, field, None)
        a = safe_attr(after, field, None)

        # AuditLogDiff besitzt nur tatsächlich geänderte Attribute.
        if hasattr(before, field) or hasattr(after, field):
            fields.append(field)

    return fields


def display_value(value) -> str:
    if value is None:
        return "—"

    if isinstance(value, discord.Colour):
        return str(value)

    if hasattr(value, "name"):
        try:
            return str(value.name)
        except Exception:
            pass

    text = str(value)

    if len(text) > 90:
        text = text[:87] + "..."

    return text


async def find_incident(guild: discord.Guild, bot_user_id: int):
    """
    Sucht die letzte zusammenhängende Redesign-/Rollback-Serie
    des DEV-Bots.

    Discord liefert Audit-Logs newest -> oldest.
    """
    matching = []

    async for entry in guild.audit_logs(
        limit=None,
        user=discord.Object(id=bot_user_id),
    ):
        if entry.user is None or entry.user.id != bot_user_id:
            continue

        if entry.action not in (
            discord.AuditLogAction.channel_update,
            discord.AuditLogAction.role_update,
        ):
            continue

        if not reason_is_redesign(entry.reason):
            continue

        matching.append(entry)

    if not matching:
        return []

    # Neueste zuerst.
    matching.sort(key=lambda e: e.created_at, reverse=True)

    # Wir nehmen nur die letzte zusammenhängende Serie.
    incident = [matching[0]]
    previous_time = matching[0].created_at

    for entry in matching[1:]:
        gap = (previous_time - entry.created_at).total_seconds()

        if gap > MAX_GAP_SECONDS:
            break

        incident.append(entry)
        previous_time = entry.created_at

    return incident


def make_preview(entries: list[discord.AuditLogEntry]) -> str:
    channel_changes = 0
    role_changes = 0

    for entry in entries:
        if entry.action == discord.AuditLogAction.channel_update:
            channel_changes += 1
        elif entry.action == discord.AuditLogAction.role_update:
            role_changes += 1

    lines = [
        "🛡️ **EHRP RECOVERY SCAN**",
        "",
        f"Gefundene zusammenhängende Änderungen: **{len(entries)}**",
        f"📁 Channel/Kategorie-Änderungen: **{channel_changes}**",
        f"🎭 Rollen-Änderungen: **{role_changes}**",
        "",
    ]

    if entries:
        newest = entries[0].created_at.astimezone()
        oldest = entries[-1].created_at.astimezone()

        lines.append(
            f"🕐 Zeitraum: **{oldest.strftime('%H:%M:%S')} "
            f"bis {newest.strftime('%H:%M:%S')}**"
        )
        lines.append("")

    lines.append("**Beispiele aus dem Audit-Log:**")
    lines.append("")

    shown = 0

    for entry in entries:
        if shown >= 12:
            break

        target = entry.target

        if target is None:
            continue

        fields = changed_fields(entry)

        if not fields:
            continue

        target_name = getattr(target, "name", f"ID {target.id}")

        for field in fields:
            if shown >= 12:
                break

            before = safe_attr(entry.before, field, None)
            after = safe_attr(entry.after, field, None)

            lines.append(
                f"• **{target_name}** — `{field}`\n"
                f"  `{display_value(after)}` → "
                f"`{display_value(before)}`"
            )

            shown += 1

    if len(entries) > shown:
        lines.append("")
        lines.append("➕ Weitere Änderungen sind im Scan enthalten.")

    lines.extend([
        "",
        "⚠️ **Noch wurde NICHTS verändert.**",
        "",
        "Mit **Recovery starten** wird zuerst der aktuelle Zustand "
        "zusätzlich gesichert und danach die gefundene Änderungsserie "
        "rückwärts abgearbeitet.",
    ])

    return "\n".join(lines)


def current_state_snapshot(guild: discord.Guild) -> dict:
    data = {
        "guild_id": guild.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "channels": [],
        "roles": [],
    }

    for channel in guild.channels:
        item = {
            "id": channel.id,
            "name": channel.name,
            "position": channel.position,
            "category_id": getattr(channel, "category_id", None),
            "type": str(channel.type),
        }

        if isinstance(channel, discord.TextChannel):
            item.update({
                "topic": channel.topic,
                "slowmode_delay": channel.slowmode_delay,
                "nsfw": channel.nsfw,
            })

        if isinstance(channel, discord.VoiceChannel):
            item.update({
                "user_limit": channel.user_limit,
                "bitrate": channel.bitrate,
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

    return data


def save_current_state(guild: discord.Guild) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    path = RECOVERY_DIR / (
        f"before_recovery_{guild.id}_{timestamp}.json"
    )

    path.write_text(
        json.dumps(
            current_state_snapshot(guild),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


async def restore_channel_entry(
    guild: discord.Guild,
    entry: discord.AuditLogEntry,
):
    target = entry.target

    if target is None:
        return False, "Kein Zielobjekt"

    channel = guild.get_channel(target.id)

    if channel is None:
        return False, f"Channel {target.id} existiert nicht mehr"

    kwargs = {}
    before = entry.before

    if hasattr(before, "name"):
        kwargs["name"] = before.name

    if hasattr(before, "topic") and isinstance(
        channel,
        discord.TextChannel,
    ):
        kwargs["topic"] = before.topic

    if hasattr(before, "slowmode_delay") and isinstance(
        channel,
        discord.TextChannel,
    ):
        kwargs["slowmode_delay"] = before.slowmode_delay

    if hasattr(before, "nsfw") and isinstance(
        channel,
        discord.TextChannel,
    ):
        kwargs["nsfw"] = before.nsfw

    if hasattr(before, "user_limit") and isinstance(
        channel,
        discord.VoiceChannel,
    ):
        kwargs["user_limit"] = before.user_limit

    if hasattr(before, "bitrate") and isinstance(
        channel,
        discord.VoiceChannel,
    ):
        kwargs["bitrate"] = before.bitrate

    if hasattr(before, "category"):
        old_category = before.category

        if old_category is None:
            kwargs["category"] = None
        else:
            kwargs["category"] = guild.get_channel(old_category.id)

    if not kwargs and not hasattr(before, "position"):
        return False, "Keine unterstützte Änderung"

    try:
        # Erst normale Eigenschaften zurücksetzen.
        if kwargs:
            await channel.edit(
                **kwargs,
                reason="EHRP Emergency Recovery",
            )

        # Position separat behandeln.
        if hasattr(before, "position"):
            await channel.edit(
                position=before.position,
                reason="EHRP Emergency Recovery",
            )

        return True, None

    except discord.Forbidden:
        return False, "Fehlende Berechtigung"

    except discord.HTTPException as exc:
        return False, f"Discord Fehler: {exc}"


async def restore_role_entry(
    guild: discord.Guild,
    entry: discord.AuditLogEntry,
):
    target = entry.target

    if target is None:
        return False, "Kein Zielobjekt"

    role = guild.get_role(target.id)

    if role is None:
        return False, f"Rolle {target.id} existiert nicht mehr"

    if role.managed:
        return False, "Managed-Rolle kann nicht bearbeitet werden"

    before = entry.before
    kwargs = {}

    if hasattr(before, "name"):
        kwargs["name"] = before.name

    if hasattr(before, "colour"):
        kwargs["colour"] = before.colour

    if hasattr(before, "hoist"):
        kwargs["hoist"] = before.hoist

    if hasattr(before, "mentionable"):
        kwargs["mentionable"] = before.mentionable

    if hasattr(before, "permissions"):
        kwargs["permissions"] = before.permissions

    try:
        if kwargs:
            await role.edit(
                **kwargs,
                reason="EHRP Emergency Recovery",
            )

        if hasattr(before, "position"):
            await guild.edit_role_positions(
                positions={
                    role: before.position
                },
                reason="EHRP Emergency Recovery",
            )

        if not kwargs and not hasattr(before, "position"):
            return False, "Keine unterstützte Änderung"

        return True, None

    except discord.Forbidden:
        return False, "Fehlende Berechtigung"

    except discord.HTTPException as exc:
        return False, f"Discord Fehler: {exc}"


async def run_recovery(
    guild: discord.Guild,
    entries: list[discord.AuditLogEntry],
):
    """
    entries liegen newest -> oldest vor.

    Genau in dieser Reihenfolge zurücksetzen:
    letzter Zustand -> davor -> davor -> ursprünglicher Zustand.
    """
    restored = 0
    failed = []

    for entry in entries:
        if entry.action == discord.AuditLogAction.channel_update:
            ok, error = await restore_channel_entry(guild, entry)

        elif entry.action == discord.AuditLogAction.role_update:
            ok, error = await restore_role_entry(guild, entry)

        else:
            ok = False
            error = "Nicht unterstützte Audit-Aktion"

        if ok:
            restored += 1
        else:
            failed.append({
                "entry_id": entry.id,
                "target": getattr(
                    entry.target,
                    "name",
                    str(getattr(entry.target, "id", "?")),
                ),
                "error": error,
            })

    return restored, failed


class RecoveryConfirmView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        guild_id: int,
    ):
        super().__init__(timeout=600)

        self.owner_id = owner_id
        self.guild_id = guild_id

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Nur der Developer, der den Recovery-Scan "
                "gestartet hat, darf das ausführen.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Recovery starten",
        emoji="🛡️",
        style=discord.ButtonStyle.danger,
    )
    async def recover_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        scan = RECOVERY_SCANS.get(self.guild_id)

        if not scan:
            await interaction.response.send_message(
                "❌ Der Recovery-Scan ist nicht mehr verfügbar. "
                "Bitte `/recovery_scan` erneut ausführen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        # Aktuellen Zustand sichern, BEVOR Recovery startet.
        backup_path = save_current_state(guild)

        restored, failed = await run_recovery(
            guild,
            scan["entries"],
        )

        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        text = [
            "🛡️ **RECOVERY BEENDET**",
            "",
            f"✅ Zurückgesetzte Audit-Schritte: **{restored}**",
            f"⚠️ Nicht automatisch möglich: **{len(failed)}**",
            "",
            "💾 Der Zustand unmittelbar vor diesem Recovery wurde "
            "zusätzlich gespeichert.",
        ]

        if failed:
            text.extend([
                "",
                "Die fehlgeschlagenen Punkte wurden **nicht blind verändert**.",
            ])

        await interaction.followup.send(
            "\n".join(text),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Abbrechen",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=(
                "❌ **Recovery abgebrochen.**\n\n"
                "Es wurde nichts verändert."
            ),
            view=self,
        )


class Recovery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="recovery_scan",
        description="Findet die letzte Redesign-Serie des DEV-Bots.",
    )
    async def recovery_scan(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        me = guild.me

        if me is None:
            await interaction.response.send_message(
                "❌ Bot-Mitglied konnte nicht gefunden werden.",
                ephemeral=True,
            )
            return

        if not me.guild_permissions.view_audit_log:
            await interaction.response.send_message(
                "❌ Mir fehlt die Berechtigung **Audit-Log anzeigen**.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        entries = await find_incident(
            guild,
            self.bot.user.id,
        )

        if not entries:
            await interaction.followup.send(
                "❌ Ich habe keine zusammenhängende "
                "Redesign-/Rollback-Serie dieses Bots gefunden.",
                ephemeral=True,
            )
            return

        RECOVERY_SCANS[guild.id] = {
            "entries": entries,
            "created_at": datetime.now(timezone.utc),
        }

        await interaction.followup.send(
            make_preview(entries),
            view=RecoveryConfirmView(
                interaction.user.id,
                guild.id,
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Recovery(bot))
