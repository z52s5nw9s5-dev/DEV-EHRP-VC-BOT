from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import BACKUP_DIR
from utils.checks import ensure_dev


DESIGN_DIR = Path(BACKUP_DIR) / "design"
DESIGN_DIR.mkdir(parents=True, exist_ok=True)

# Pro Server merken wir uns, welcher Stil zuletzt vorgeschlagen wurde.
STYLE_INDEX = {}

STYLES = [
    {
        "name": "🔥 EHRP Premium",
        "channel_sep": "・",
        "category_left": "╭・",
        "category_upper": True,
    },
    {
        "name": "⚡ Modern RP",
        "channel_sep": "〢",
        "category_left": "〢 ",
        "category_upper": True,
    },
    {
        "name": "💎 Elegant",
        "channel_sep": "┃",
        "category_left": "┏・",
        "category_upper": True,
    },
    {
        "name": "✨ Clean",
        "channel_sep": "・",
        "category_left": "— ",
        "category_upper": False,
    },
]


EMOJIS = [
    (("regel", "rules"), "📜"),
    (("ankünd", "ankuend", "news"), "📢"),
    (("info", "information"), "📌"),
    (("willkommen", "welcome"), "👋"),
    (("chat", "allgemein", "general"), "💬"),
    (("support", "hilfe", "ticket"), "🎫"),
    (("bewerbung", "apply"), "📝"),
    (("team", "personal"), "👥"),
    (("leitung", "vorstand", "führung"), "👑"),
    (("developer", "dev"), "🛠️"),
    (("log", "protokoll"), "📋"),
    (("bot",), "🤖"),
    (("voice", "talk", "sprach", "besprechung"), "🔊"),
    (("musik", "music"), "🎵"),
    (("event",), "🎉"),
    (("partner",), "🤝"),
    (("rolle", "role"), "🎭"),
    (("abwesen",), "🌴"),
    (("stats", "statistik"), "📊"),
    (("backup",), "💾"),
    (("bewerber",), "📨"),
    (("beschwerde",), "⚠️"),
    (("leitung",), "👑"),
    (("schulung", "training"), "🎓"),
    (("meeting", "sitzung"), "📅"),
]


def emoji_for(name: str) -> str:
    low = name.lower()
    for words, emoji in EMOJIS:
        if any(word in low for word in words):
            return emoji
    return "💠"


def strip_design(name: str) -> str:
    """Entfernt typische alte Dekoration am Anfang."""
    name = name.strip()

    # Unicode-Deko / Trenner
    name = re.sub(r"^[╭╰┏┗┌└├┠┃│┊〢・»›—\-_=|\s]+", "", name)

    # Ein oder mehrere Emoji-Blöcke am Anfang
    name = re.sub(
        r"^[^\w\s]{1,5}\s*[・┃│┊〢»›—\-]*\s*",
        "",
        name,
        flags=re.UNICODE,
    )

    return name.strip()


def make_channel_name(name: str, style: dict) -> str:
    base = strip_design(name)
    base = base.replace("_", " ")
    base = re.sub(r"\s+", " ", base).strip()
    base = base.lower().replace(" ", "-")
    base = re.sub(r"-{2,}", "-", base)

    emoji = emoji_for(base)
    return f"{emoji}{style['channel_sep']}{base}"[:100]


def make_category_name(name: str, style: dict) -> str:
    base = strip_design(name)
    base = base.replace("_", " ")
    base = re.sub(r"\s+", " ", base).strip()

    if style["category_upper"]:
        base = base.upper()

    emoji = emoji_for(base)
    return f"{style['category_left']}{emoji} {base}"[:100]


def topic_for(channel: discord.TextChannel) -> str | None:
    """
    Nur leere Topics ergänzen.
    Vorhandene Topics werden NICHT überschrieben.
    """
    if channel.topic:
        return channel.topic

    low = channel.name.lower()

    if "regel" in low:
        return "📜 Alle wichtigen Regeln und Vorgaben des Servers."
    if "ankünd" in low or "news" in low:
        return "📢 Offizielle Neuigkeiten und Ankündigungen."
    if "support" in low or "hilfe" in low:
        return "🎫 Fragen, Hilfe und Support."
    if "bewerb" in low:
        return "📝 Informationen und Inhalte rund um Bewerbungen."
    if "team" in low:
        return "👥 Interner Bereich für das Team."
    if "chat" in low or "allgemein" in low:
        return "💬 Allgemeiner Austausch der Community."

    return None


def snapshot_file(guild_id: int) -> Path:
    return DESIGN_DIR / f"before_{guild_id}.json"


def save_snapshot(guild: discord.Guild) -> Path:
    data = {
        "version": 1,
        "guild_id": guild.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "categories": [],
        "channels": [],
    }

    for cat in guild.categories:
        data["categories"].append({
            "id": cat.id,
            "name": cat.name,
            "position": cat.position,
        })

    for ch in guild.channels:
        if isinstance(ch, discord.CategoryChannel):
            continue

        item = {
            "id": ch.id,
            "name": ch.name,
            "position": ch.position,
            "category_id": ch.category_id,
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
            })

        data["channels"].append(item)

    path = snapshot_file(guild.id)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def build_plan(guild: discord.Guild, style_index: int):
    style = STYLES[style_index]
    plan = []

    # Kategorien
    for cat in guild.categories:
        new_name = make_category_name(cat.name, style)

        if new_name != cat.name:
            plan.append({
                "kind": "category_name",
                "id": cat.id,
                "before": cat.name,
                "after": new_name,
            })

    # Channels
    for ch in guild.channels:
        if isinstance(ch, discord.CategoryChannel):
            continue

        if not isinstance(
            ch,
            (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.ForumChannel,
                discord.StageChannel,
            ),
        ):
            continue

        new_name = make_channel_name(ch.name, style)

        if new_name != ch.name:
            plan.append({
                "kind": "channel_name",
                "id": ch.id,
                "before": ch.name,
                "after": new_name,
            })

        if isinstance(ch, discord.TextChannel):
            new_topic = topic_for(ch)

            if new_topic and new_topic != ch.topic:
                plan.append({
                    "kind": "topic",
                    "id": ch.id,
                    "before": ch.topic or "Kein Topic",
                    "after": new_topic,
                })

    return plan


def preview(plan, style_index):
    style = STYLES[style_index]

    lines = [
        f"✨ **SERVER REDESIGN — {style['name']}**",
        "",
        "🔒 **Noch wurde NICHTS verändert.**",
        "",
    ]

    if not plan:
        lines.append("Keine sinnvollen Änderungen gefunden.")
        return "\n".join(lines)

    shown = 0

    for item in plan:
        if shown >= 22:
            break

        if item["kind"] == "category_name":
            icon = "📁"
        elif item["kind"] == "topic":
            icon = "📝"
        else:
            icon = "＃"

        lines.append(
            f"{icon} `{item['before']}`\n"
            f"↳ `{item['after']}`"
        )
        shown += 1

    if len(plan) > shown:
        lines.append(
            f"\n➕ **{len(plan) - shown} weitere Änderungen**"
        )

    lines.extend([
        "",
        f"🛠️ Insgesamt: **{len(plan)} Änderungen**",
        "",
        "✅ **Übernehmen**",
        "🔄 **Anderes Design**",
        "❌ **Abbrechen**",
    ])

    return "\n".join(lines)


async def restore(guild: discord.Guild):
    path = snapshot_file(guild.id)

    if not path.exists():
        return 0, ["Kein Snapshot vorhanden."]

    data = json.loads(path.read_text(encoding="utf-8"))

    restored = 0
    errors = []

    # Kategorien
    for saved in data.get("categories", []):
        obj = guild.get_channel(saved["id"])

        if not isinstance(obj, discord.CategoryChannel):
            errors.append(f"Kategorie fehlt: {saved['name']}")
            continue

        try:
            await obj.edit(
                name=saved["name"],
                position=saved["position"],
                reason="EHRP Redesign Rollback",
            )
            restored += 1
        except discord.HTTPException:
            errors.append(saved["name"])

    # Channels
    for saved in data.get("channels", []):
        obj = guild.get_channel(saved["id"])

        if obj is None:
            errors.append(f"Channel fehlt: {saved['name']}")
            continue

        kwargs = {
            "name": saved["name"],
            "position": saved["position"],
            "category": (
                guild.get_channel(saved["category_id"])
                if saved.get("category_id")
                else None
            ),
            "reason": "EHRP Redesign Rollback",
        }

        if isinstance(obj, discord.TextChannel):
            kwargs.update({
                "topic": saved.get("topic"),
                "slowmode_delay": saved.get("slowmode_delay", 0),
                "nsfw": saved.get("nsfw", False),
            })

        if isinstance(obj, discord.VoiceChannel):
            kwargs["user_limit"] = saved.get("user_limit", 0)

        try:
            await obj.edit(**kwargs)
            restored += 1
        except discord.HTTPException:
            errors.append(saved["name"])

    return restored, errors


class RollbackView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=1800)
        self.owner_id = owner_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Das kann nur der Developer machen, "
                "der das Redesign gestartet hat.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Alles zurücksetzen",
        emoji="↩️",
        style=discord.ButtonStyle.danger,
    )
    async def rollback(self, interaction, button):
        await interaction.response.defer(ephemeral=True)

        count, errors = await restore(interaction.guild)

        button.disabled = True

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        text = (
            "↩️ **REDESIGN ZURÜCKGESETZT**\n\n"
            f"✅ Wiederhergestellt: **{count} Elemente**"
        )

        if errors:
            text += (
                f"\n⚠️ Nicht vollständig wiederhergestellt: "
                f"**{len(errors)}**"
            )

        await interaction.followup.send(text, ephemeral=True)


class RedesignView(discord.ui.View):
    def __init__(self, owner_id: int, guild_id: int, style_index: int):
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.guild_id = guild_id
        self.style_index = style_index

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Nur der Developer, der das Redesign gestartet hat, "
                "kann diese Auswahl benutzen.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Übernehmen",
        emoji="✅",
        style=discord.ButtonStyle.success,
    )
    async def apply(self, interaction, button):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True)

        # Plan direkt vor Anwendung NEU erstellen.
        plan = build_plan(guild, self.style_index)

        # Snapshot unmittelbar davor.
        save_snapshot(guild)

        changed = 0
        errors = []

        for item in plan:
            obj = guild.get_channel(item["id"])

            if obj is None:
                errors.append(item["before"])
                continue

            try:
                if item["kind"] in ("category_name", "channel_name"):
                    await obj.edit(
                        name=item["after"],
                        reason=f"EHRP Server Redesign durch {interaction.user}",
                    )

                elif item["kind"] == "topic":
                    if isinstance(obj, discord.TextChannel):
                        await obj.edit(
                            topic=item["after"],
                            reason=f"EHRP Server Redesign durch {interaction.user}",
                        )

                changed += 1

            except discord.HTTPException:
                errors.append(item["before"])

        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        text = (
            f"✅ **{STYLES[self.style_index]['name']} übernommen**\n\n"
            f"✨ Erfolgreiche Änderungen: **{changed}**\n"
            f"💾 Zustand davor wurde gespeichert.\n\n"
            f"Gefällt es dir live doch nicht? "
            f"Unten kannst du alles zurücksetzen."
        )

        if errors:
            text += (
                f"\n\n⚠️ **{len(errors)} Änderungen** "
                "konnten nicht ausgeführt werden."
            )

        await interaction.followup.send(
            text,
            view=RollbackView(self.owner_id),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Anderes Design",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
    )
    async def another(self, interaction, button):
        new_index = (self.style_index + 1) % len(STYLES)

        STYLE_INDEX[self.guild_id] = new_index

        plan = build_plan(interaction.guild, new_index)

        new_view = RedesignView(
            self.owner_id,
            self.guild_id,
            new_index,
        )

        await interaction.response.edit_message(
            content=preview(plan, new_index),
            view=new_view,
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
            content=(
                "❌ **Redesign abgebrochen.**\n\n"
                "Am Server wurde nichts verändert."
            ),
            view=self,
        )


class Design(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="server_redesign",
        description="Plant ein komplettes neues Server-Design mit Vorschau.",
    )
    async def server_redesign(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction):
            return

        guild = interaction.guild

        if guild is None:
            return

        index = STYLE_INDEX.get(guild.id, 0)
        plan = build_plan(guild, index)

        await interaction.response.send_message(
            preview(plan, index),
            view=RedesignView(
                interaction.user.id,
                guild.id,
                index,
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="redesign_zurueck",
        description="Setzt das letzte Server-Redesign zurück.",
    )
    async def redesign_zurueck(self, interaction: discord.Interaction):
        if not await ensure_dev(interaction):
            return

        if not snapshot_file(interaction.guild.id).exists():
            await interaction.response.send_message(
                "❌ Es wurde noch kein Redesign-Backup gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        count, errors = await restore(interaction.guild)

        text = (
            "↩️ **LETZTES REDESIGN ZURÜCKGESETZT**\n\n"
            f"✅ Wiederhergestellt: **{count} Elemente**"
        )

        if errors:
            text += f"\n⚠️ Probleme: **{len(errors)}**"

        await interaction.followup.send(text, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Design(bot))
