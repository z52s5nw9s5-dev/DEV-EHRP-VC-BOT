from __future__ import annotations

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import ensure_dev


RECOVERY_REASON_WORDS = (
    "redesign",
    "design rollback",
    "server redesign",
    "ehrp redesign",
)


def is_recovery_related(entry: discord.AuditLogEntry) -> bool:
    reason = (entry.reason or "").lower()
    return any(word in reason for word in RECOVERY_REASON_WORDS)


async def collect_changes(guild: discord.Guild, bot_id: int):
    entries = []

    async for entry in guild.audit_logs(
        limit=None,
        user=discord.Object(id=bot_id),
    ):
        if entry.user is None:
            continue

        if entry.user.id != bot_id:
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


def build_original_states(entries):
    entries = sorted(entries, key=lambda e: e.created_at)

    objects = {}

    supported_fields = (
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

    for entry in entries:
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
            }

        item = objects[target_id]
        before = entry.before

        for field in supported_fields:
            if field in item["fields"]:
                continue

            if not hasattr(before, field):
                continue

            value = getattr(before, field)

            if field == "category":
                value = value.id if value is not None else None

            elif field == "colour":
                value = value.value if value is not None else 0

            elif field == "permissions":
                value = value.value if value is not None else 0

            item["fields"][field] = value

    return objects


async def restore_channel(guild: discord.Guild, item: dict):
    channel = guild.get_channel(item["id"])

    if channel is None:
        return False

    fields = item["fields"]
    kwargs = {}

    if "name" in fields:
        kwargs["name"] = fields["name"]

    if isinstance(channel, discord.TextChannel):
        if "topic" in fields:
            kwargs["topic"] = fields["topic"]

        if "slowmode_delay" in fields:
            kwargs["slowmode_delay"] = fields["slowmode_delay"]

        if "nsfw" in fields:
            kwargs["nsfw"] = fields["nsfw"]

    if isinstance(channel, discord.VoiceChannel):
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
            await channel.edit(
                **kwargs,
                reason="EHRP FINAL RECOVERY",
            )

        if "position" in fields:
            await channel.edit(
                position=fields["position"],
                reason="EHRP FINAL RECOVERY",
            )

        return True

    except Exception as error:
        print(f"Channel recovery failed {channel.id}: {error}")
        return False


async def restore_role(guild: discord.Guild, item: dict):
    role = guild.get_role(item["id"])

    if role is None:
        return False

    if role.managed:
        return False

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
                reason="EHRP FINAL RECOVERY",
            )

        if "position" in fields:
            await guild.edit_role_positions(
                positions={
                    role: fields["position"]
                },
                reason="EHRP FINAL RECOVERY",
            )

        return True

    except Exception as error:
        print(f"Role recovery failed {role.id}: {error}")
        return False


class RecoveryConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, plan: dict):
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.plan = plan

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Nur du kannst die Recovery bestätigen.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="JA – ALLES ZURÜCKSETZEN",
        emoji="↩️",
        style=discord.ButtonStyle.danger,
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.defer(ephemeral=True)

        restored = 0
        failed = 0

        for item in self.plan.values():
            if item["type"] == "channel":
                ok = await restore_channel(
                    interaction.guild,
                    item,
                )
            else:
                ok = await restore_role(
                    interaction.guild,
                    item,
                )

            if ok:
                restored += 1
            else:
                failed += 1

            await asyncio.sleep(0.5)

        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.followup.send(
            (
                "✅ **RECOVERY BEENDET**\n\n"
                f"↩️ Wiederhergestellt: **{restored}**\n"
                f"⚠️ Nicht möglich: **{failed}**"
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Abbrechen",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
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
        name="alles_zuruecksetzen",
        description="Stellt den Zustand vor dem DEV-Redesign wieder her.",
    )
    async def alles_zuruecksetzen(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        bot_member = guild.me

        if bot_member is None:
            await interaction.response.send_message(
                "❌ Bot-Mitglied konnte nicht gefunden werden.",
                ephemeral=True,
            )
            return

        if not bot_member.guild_permissions.view_audit_log:
            await interaction.response.send_message(
                "❌ Dem Bot fehlt **Audit-Log anzeigen**.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        entries = await collect_changes(
            guild,
            self.bot.user.id,
        )

        if not entries:
            await interaction.followup.send(
                "❌ Keine Redesign-/Rollback-Änderungen gefunden.",
                ephemeral=True,
            )
            return

        plan = build_original_states(entries)

        channel_count = sum(
            1
            for item in plan.values()
            if item["type"] == "channel"
        )

        role_count = sum(
            1
            for item in plan.values()
            if item["type"] == "role"
        )

        await interaction.followup.send(
            (
                "🛡️ **ALLES ZURÜCKSETZEN**\n\n"
                f"Gefundene Audit-Einträge: **{len(entries)}**\n"
                f"📁 Channels/Kategorien: **{channel_count}**\n"
                f"🎭 Rollen: **{role_count}**\n\n"
                "Der Bot nimmt pro Objekt den ältesten bekannten "
                "Zustand vor dem Redesign.\n\n"
                "⚠️ Noch wurde nichts verändert."
            ),
            view=RecoveryConfirmView(
                interaction.user.id,
                plan,
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Recovery(bot))
