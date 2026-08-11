from __future__ import annotations

from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import ensure_dev


# Wie groß darf die Pause zwischen Änderungen sein,
# damit sie noch als derselbe Block gelten?
BLOCK_GAP = timedelta(minutes=10)

# Wir speichern nur Scans im RAM.
RECOVERY_SCANS = {}


def is_our_design_action(entry: discord.AuditLogEntry) -> bool:
    """
    Erkennt Änderungen, die zu unserem Design-/Rollback-System gehören.
    """
    reason = (entry.reason or "").lower()

    keywords = (
        "redesign",
        "design",
        "rollback",
        "ehrp",
    )

    return any(word in reason for word in keywords)


def target_name(entry: discord.AuditLogEntry) -> str:
    target = entry.target

    if target is None:
        return "Unbekannt"

    return getattr(target, "name", f"ID {getattr(target, 'id', '?')}")


def split_into_blocks(entries):
    """
    Discord liefert newest -> oldest.
    Wir gruppieren Änderungen anhand ihrer Zeitabstände.
    """
    if not entries:
        return []

    entries = sorted(
        entries,
        key=lambda e: e.created_at,
        reverse=True,
    )

    blocks = []
    current = [entries[0]]

    for previous, entry in zip(entries, entries[1:]):
        gap = previous.created_at - entry.created_at

        if gap <= BLOCK_GAP:
            current.append(entry)
        else:
            blocks.append(current)
            current = [entry]

    blocks.append(current)

    return blocks


async def collect_design_entries(
    guild: discord.Guild,
    bot_id: int,
):
    """
    Holt ALLE noch im Discord Audit-Log vorhandenen
    Channel-/Rollenänderungen unseres Bots, die nach
    Design/Redesign/Rollback aussehen.
    """
    found = []

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

        if not is_our_design_action(entry):
            continue

        found.append(entry)

    return found


def count_types(block):
    channels = sum(
        1
        for e in block
        if e.action == discord.AuditLogAction.channel_update
    )

    roles = sum(
        1
        for e in block
        if e.action == discord.AuditLogAction.role_update
    )

    return channels, roles


def reason_summary(block):
    reasons = []

    for entry in block:
        reason = entry.reason or "Kein Grund"

        if reason not in reasons:
            reasons.append(reason)

    return reasons[:3]


class BlockSelect(discord.ui.Select):
    def __init__(self, blocks):
        self.blocks = blocks

        options = []

        for index, block in enumerate(blocks[:25], start=1):
            newest = block[0].created_at.astimezone()
            oldest = block[-1].created_at.astimezone()

            channels, roles = count_types(block)

            label = (
                f"Block {index} • {len(block)} Änderungen"
            )

            description = (
                f"{oldest.strftime('%H:%M')}–"
                f"{newest.strftime('%H:%M')} • "
                f"{channels} Ch / {roles} Rollen"
            )

            options.append(
                discord.SelectOption(
                    label=label[:100],
                    description=description[:100],
                    value=str(index - 1),
                    emoji="🛡️",
                )
            )

        super().__init__(
            placeholder="Änderungsblock auswählen …",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        block_index = int(self.values[0])

        scan = RECOVERY_SCANS.get(interaction.guild_id)

        if not scan:
            await interaction.response.send_message(
                "❌ Scan nicht mehr vorhanden. "
                "Bitte `/recovery_scan` erneut ausführen.",
                ephemeral=True,
            )
            return

        block = scan["blocks"][block_index]

        newest = block[0].created_at.astimezone()
        oldest = block[-1].created_at.astimezone()

        channels, roles = count_types(block)

        reasons = reason_summary(block)

        lines = [
            f"🛡️ **BLOCK {block_index + 1}**",
            "",
            f"Änderungen: **{len(block)}**",
            f"📁 Channels/Kategorien: **{channels}**",
            f"🎭 Rollen: **{roles}**",
            "",
            (
                f"🕐 Zeitraum: "
                f"**{oldest.strftime('%H:%M:%S')} bis "
                f"{newest.strftime('%H:%M:%S')}**"
            ),
            "",
            "📝 **Audit-Gründe:**",
        ]

        for reason in reasons:
            lines.append(f"• `{reason}`")

        lines.extend([
            "",
            "🔎 **Einige betroffene Objekte:**",
        ])

        shown = set()

        for entry in block:
            name = target_name(entry)

            if name in shown:
                continue

            shown.add(name)
            lines.append(f"• {name}")

            if len(shown) >= 12:
                break

        lines.extend([
            "",
            "⚠️ **Es wurde NICHTS verändert.**",
            "",
            "Dieser Bildschirm dient nur zur Analyse.",
        ])

        await interaction.response.send_message(
            "\n".join(lines),
            ephemeral=True,
        )


class BlockView(discord.ui.View):
    def __init__(self, blocks):
        super().__init__(timeout=900)

        self.add_item(BlockSelect(blocks))


class Recovery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="recovery_scan",
        description="Analysiert alle Design-Änderungen des DEV-Bots.",
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
                "❌ Bot konnte auf dem Server nicht gefunden werden.",
                ephemeral=True,
            )
            return

        if not me.guild_permissions.view_audit_log:
            await interaction.response.send_message(
                "❌ Mir fehlt **Audit-Log anzeigen**.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        entries = await collect_design_entries(
            guild,
            self.bot.user.id,
        )

        if not entries:
            await interaction.followup.send(
                "❌ Keine passenden Design-/Rollback-Änderungen "
                "dieses Bots gefunden.",
                ephemeral=True,
            )
            return

        blocks = split_into_blocks(entries)

        RECOVERY_SCANS[guild.id] = {
            "blocks": blocks,
            "created_at": datetime.now(timezone.utc),
        }

        lines = [
            "🛡️ **EHRP RECOVERY ANALYSE**",
            "",
            f"Gesamte gefundene Änderungen: **{len(entries)}**",
            f"Gefundene Änderungsblöcke: **{len(blocks)}**",
            "",
            "━━━━━━━━━━━━━━━━━━",
        ]

        for index, block in enumerate(blocks[:20], start=1):
            newest = block[0].created_at.astimezone()
            oldest = block[-1].created_at.astimezone()

            channels, roles = count_types(block)

            lines.extend([
                "",
                f"**Block {index}**",
                (
                    f"🕐 {oldest.strftime('%H:%M:%S')} – "
                    f"{newest.strftime('%H:%M:%S')}"
                ),
                f"🔧 **{len(block)} Änderungen**",
                f"📁 {channels} Channel • 🎭 {roles} Rollen",
            ])

            reasons = reason_summary(block)

            if reasons:
                lines.append(
                    f"📝 `{reasons[0]}`"
                )

        if len(blocks) > 20:
            lines.extend([
                "",
                f"➕ {len(blocks) - 20} weitere Blöcke",
            ])

        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━",
            "",
            "⚠️ **REINER ANALYSE-MODUS**",
            "Dieser Command kann aktuell überhaupt nichts "
            "am Server verändern.",
            "",
            "Wähle unten einen Block aus, um ihn genauer anzusehen.",
        ])

        await interaction.followup.send(
            "\n".join(lines),
            view=BlockView(blocks),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Recovery(bot))
