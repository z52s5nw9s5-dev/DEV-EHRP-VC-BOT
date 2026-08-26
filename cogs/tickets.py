from __future__ import annotations

import io
import re
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import ensure_dev


# ============================================================
# EHRP | SYSTEM — TICKET CONFIG
# ============================================================

PANEL_CHANNEL_ID = 1526943324672364606
TICKET_LOG_CHANNEL_ID = 1526986104207704196

SYSTEM_COLOR = 0x5865F2
OPEN_COLOR = 0x57F287
CLAIMED_COLOR = 0xFEE75C
CLOSED_COLOR = 0xED4245


TICKET_TYPES = {
    "highteam": {
        "name": "High Team",
        "emoji": "⭐",
        "description": "Vertrauliche Anliegen für das High Team.",
        "category_id": 1526978181591207986,
        "role_id": 1526955340414058526,
    },
    "allgemein": {
        "name": "Allgemein",
        "emoji": "🎫",
        "description": "Fragen, Probleme und allgemeiner Support.",
        "category_id": 1526938849618432000,
        "role_id": 1526956922555732151,
    },
    "entbannung": {
        "name": "Entbannung",
        "emoji": "🔓",
        "description": "Anträge auf Entbannung.",
        "category_id": 1526938782732124201,
        "role_id": 1526955621981753435,
    },
    "immobilien": {
        "name": "Immobilien",
        "emoji": "🏠",
        "description": "Anliegen rund um Immobilien.",
        "category_id": 1526938582772875404,
        "role_id": 1526956922555732151,
    },
    "socialmedia": {
        "name": "Social Media",
        "emoji": "📱",
        "description": "Social Media, Content und Medien.",
        "category_id": 1526938931013222570,
        "role_id": 1526956524466081802,
    },
    "developer": {
        "name": "Developer",
        "emoji": "💻",
        "description": "Technische Probleme, Bugs und Entwicklung.",
        "category_id": 1526980142054903969,
        "role_id": 1526955429697949706,
    },
    "fraktion": {
        "name": "Fraktion",
        "emoji": "🏛️",
        "description": "Fraktionsbezogene Anliegen.",
        "category_id": 1526982043009941564,
        "role_id": 1532505422752383048,
    },
}


# ============================================================
# HELPERS
# ============================================================

def slugify(value: str) -> str:
    value = value.strip().lower()

    value = (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )

    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)

    return value.strip("-")[:40] or "user"


def make_topic(
    ticket_type: str,
    owner_id: int,
    claimed_id: int = 0,
    control_id: int = 0,
    status: str = "open",
) -> str:

    return (
        "EHRP_TICKET|"
        f"type={ticket_type}|"
        f"owner={owner_id}|"
        f"claimed={claimed_id}|"
        f"control={control_id}|"
        f"status={status}"
    )


def read_topic(channel: discord.TextChannel) -> dict | None:

    topic = channel.topic or ""

    if not topic.startswith("EHRP_TICKET|"):
        return None

    parts = {}

    for chunk in topic.split("|")[1:]:

        if "=" not in chunk:
            continue

        key, value = chunk.split("=", 1)
        parts[key] = value

    try:
        return {
            "type": parts["type"],
            "owner_id": int(parts["owner"]),
            "claimed_id": int(parts.get("claimed", "0")),
            "control_id": int(parts.get("control", "0")),
            "status": parts.get("status", "open"),
        }

    except (KeyError, ValueError):
        return None


def get_config(channel: discord.TextChannel):

    meta = read_topic(channel)

    if not meta:
        return None, None

    return meta, TICKET_TYPES.get(meta["type"])


def is_staff(
    interaction: discord.Interaction,
    config: dict,
) -> bool:

    if not isinstance(
        interaction.user,
        discord.Member,
    ):
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    role = interaction.guild.get_role(
        config["role_id"]
    )

    return (
        role is not None
        and role in interaction.user.roles
    )


async def resolve_member(
    guild: discord.Guild,
    user_id: int,
):

    member = guild.get_member(user_id)

    if member:
        return member

    try:
        return await guild.fetch_member(user_id)

    except discord.HTTPException:
        return None


async def get_control_message(
    channel: discord.TextChannel,
    meta: dict,
):

    control_id = meta.get("control_id", 0)

    if control_id:

        try:
            return await channel.fetch_message(
                control_id
            )

        except discord.HTTPException:
            pass

    try:

        async for message in channel.history(
            limit=30
        ):

            if (
                message.author.bot
                and message.embeds
                and "EHRP | TICKET"
                in (message.embeds[0].title or "")
            ):
                return message

    except discord.HTTPException:
        pass

    return None


async def send_log(
    guild: discord.Guild,
    title: str,
    description: str,
    color: int = SYSTEM_COLOR,
    file: discord.File | None = None,
):

    channel = guild.get_channel(
        TICKET_LOG_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):

        print(
            "⚠️ Ticket-Log-Channel wurde nicht gefunden."
        )

        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    embed.set_footer(
        text="EHRP | System • Ticket Logging"
    )

    try:

        if file is None:
            await channel.send(
                embed=embed
            )

        else:
            await channel.send(
                embed=embed,
                file=file,
            )

    except discord.HTTPException as error:

        print(
            f"❌ Ticket-Log Fehler: {error}"
        )


async def make_transcript(
    channel: discord.TextChannel,
):

    lines = [
        "EHRP | SYSTEM — TICKET TRANSCRIPT",
        f"Ticket: #{channel.name}",
        f"Channel-ID: {channel.id}",
        "",
        "=" * 60,
        "",
    ]

    try:

        async for message in channel.history(
            limit=1000,
            oldest_first=True,
        ):

            timestamp = (
                message.created_at.strftime(
                    "%d.%m.%Y %H:%M:%S UTC"
                )
            )

            content = message.content or ""

            if message.attachments:

                attachments = " | ".join(
                    attachment.url
                    for attachment
                    in message.attachments
                )

                content = (
                    f"{content} | "
                    f"Anhänge: {attachments}"
                ).strip(" |")

            if (
                not content
                and message.embeds
            ):
                content = (
                    "[Embed / System-Nachricht]"
                )

            if not content:
                content = "[Keine Textnachricht]"

            lines.append(
                f"[{timestamp}] "
                f"{message.author} "
                f"({message.author.id}): "
                f"{content}"
            )

    except discord.HTTPException as error:

        print(
            f"❌ Transcript Fehler: {error}"
        )

        return None

    payload = "\n".join(
        lines
    ).encode("utf-8")

    return discord.File(
        io.BytesIO(payload),
        filename=(
            f"{channel.name}-transcript.txt"
        ),
    )


def copy_fields(
    source: discord.Embed | None,
    target: discord.Embed,
):

    if not source:
        return

    for field in source.fields:

        target.add_field(
            name=field.name,
            value=field.value,
            inline=field.inline,
        )


async def build_ticket_embed(
    channel: discord.TextChannel,
    meta: dict,
    config: dict,
    previous: discord.Embed | None = None,
    close_reason: str | None = None,
):

    guild = channel.guild

    owner = await resolve_member(
        guild,
        meta["owner_id"],
    )

    claimer = None

    if meta["claimed_id"]:

        claimer = await resolve_member(
            guild,
            meta["claimed_id"],
        )

    staff_role = guild.get_role(
        config["role_id"]
    )

    status = meta.get(
        "status",
        "open",
    )

    if status == "closed":

        status_text = "🔴 Geschlossen"
        color = CLOSED_COLOR

    elif meta["claimed_id"]:

        status_text = "🟡 In Bearbeitung"
        color = CLAIMED_COLOR

    else:

        status_text = "🟢 Offen"
        color = OPEN_COLOR

    if owner:

        owner_text = owner.mention

    else:

        owner_text = (
            f"<@{meta['owner_id']}>"
        )

    if claimer:

        claimer_text = claimer.mention

    else:

        claimer_text = (
            "Nicht übernommen"
        )

    if staff_role:

        role_text = staff_role.mention

    else:

        role_text = (
            "Rolle nicht gefunden"
        )

    description = (
        "### SERVICE SESSION\n\n"
        f"**Status:** {status_text}\n"
        f"**Bereich:** "
        f"{config['emoji']} "
        f"{config['name']}\n"
        f"**Ersteller:** {owner_text}\n"
        f"**Zuständig:** {role_text}\n"
        f"**Bearbeiter:** {claimer_text}"
    )

    if close_reason:

        description += (
            f"\n**Schließgrund:** "
            f"{close_reason}"
        )

    embed = discord.Embed(
        title=(
            f"{config['emoji']} "
            "EHRP | TICKET"
        ),
        description=description,
        color=color,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    if owner:

        embed.set_author(
            name=owner.display_name,
            icon_url=(
                owner.display_avatar.url
            ),
        )

        embed.set_thumbnail(
            url=owner.display_avatar.url
        )

    copy_fields(
        previous,
        embed,
    )

    embed.set_footer(
        text=(
            "EHRP | System • "
            "Ticket Control"
        )
    )

    return embed


async def find_open_ticket(
    guild: discord.Guild,
    owner_id: int,
    ticket_type: str,
):

    config = TICKET_TYPES[
        ticket_type
    ]

    category = guild.get_channel(
        config["category_id"]
    )

    if not isinstance(
        category,
        discord.CategoryChannel,
    ):
        return None

    for channel in category.text_channels:

        meta = read_topic(channel)

        if not meta:
            continue

        if (
            meta["owner_id"]
            == owner_id
            and meta["type"]
            == ticket_type
            and meta["status"]
            != "closed"
        ):
            return channel

    return None


# ============================================================
# MAIN PANEL
# ============================================================

def build_main_panel():

    embed = discord.Embed(
        title="EHRP | SERVICE CENTER",
        description=(
            "### DIGITAL SERVICE PORTAL\n\n"
            "Wähle unten den Bereich aus, "
            "der zu deinem Anliegen passt.\n\n"
            "🟢 **System:** Online\n"
            "🔒 **Tickets:** Privat\n"
            "⚡ **Routing:** Automatisch\n"
            "🛡️ **Logging:** Aktiv"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_author(
        name="EHRP | SYSTEM"
    )

    embed.set_footer(
        text=(
            "EHRP | System • "
            "Service Portal"
        )
    )

    return embed


class TicketSelect(
    discord.ui.Select
):

    def __init__(self):

        options = []

        for key, config in (
            TICKET_TYPES.items()
        ):

            options.append(
                discord.SelectOption(
                    label=config["name"],
                    value=key,
                    emoji=config["emoji"],
                    description=(
                        config[
                            "description"
                        ][:100]
                    ),
                )
            )

        super().__init__(
            placeholder=(
                "Abteilung auswählen …"
            ),
            min_values=1,
            max_values=1,
            options=options,
            custom_id=(
                "ehrp:ticket:type_select"
            ),
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):

        await (
            interaction.response.send_modal(
                TicketCreateModal(
                    self.values[0]
                )
            )
        )


class TicketPanelView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


# ============================================================
# CREATE TICKET
# ============================================================

class TicketCreateModal(
    discord.ui.Modal
):

    def __init__(
        self,
        ticket_type: str,
    ):

        self.ticket_type = (
            ticket_type
        )

        config = TICKET_TYPES[
            ticket_type
        ]

        super().__init__(
            title=(
                f"{config['name']} • "
                "Ticket"
            )
        )

        if (
            ticket_type
            == "entbannung"
        ):

            fields = [
                discord.ui.TextInput(
                    label="Ingame-Name",
                    placeholder=(
                        "Dein RP-/Ingame-Name"
                    ),
                    max_length=100,
                ),
                discord.ui.TextInput(
                    label="Banngrund",
                    placeholder=(
                        "Warum wurdest du "
                        "gebannt?"
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=700,
                ),
                discord.ui.TextInput(
                    label=(
                        "Entbannungsbegründung"
                    ),
                    placeholder=(
                        "Warum sollten wir "
                        "dich entbannen?"
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1200,
                ),
            ]

        elif (
            ticket_type
            == "developer"
        ):

            fields = [
                discord.ui.TextInput(
                    label="Fehler / System",
                    placeholder=(
                        "Was funktioniert "
                        "nicht?"
                    ),
                    max_length=150,
                ),
                discord.ui.TextInput(
                    label="Beschreibung",
                    placeholder=(
                        "Beschreibe den Fehler "
                        "möglichst genau."
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1500,
                ),
            ]

        elif (
            ticket_type
            == "immobilien"
        ):

            fields = [
                discord.ui.TextInput(
                    label="Immobilie / Ort",
                    placeholder=(
                        "Welche Immobilie "
                        "betrifft das Anliegen?"
                    ),
                    max_length=150,
                ),
                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder=(
                        "Beschreibe dein "
                        "Anliegen."
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1500,
                ),
            ]

        elif (
            ticket_type
            == "socialmedia"
        ):

            fields = [
                discord.ui.TextInput(
                    label=(
                        "Plattform / Thema"
                    ),
                    placeholder=(
                        "TikTok, YouTube, "
                        "Instagram, Kooperation …"
                    ),
                    max_length=150,
                ),
                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder=(
                        "Beschreibe dein "
                        "Anliegen."
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1500,
                ),
            ]

        elif (
            ticket_type
            == "fraktion"
        ):

            fields = [
                discord.ui.TextInput(
                    label="Fraktion",
                    placeholder=(
                        "Welche Fraktion "
                        "betrifft dein Anliegen?"
                    ),
                    max_length=150,
                ),
                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder=(
                        "Beschreibe dein "
                        "Anliegen."
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1500,
                ),
            ]

        else:

            fields = [
                discord.ui.TextInput(
                    label="Betreff",
                    placeholder=(
                        "Worum geht es?"
                    ),
                    max_length=150,
                ),
                discord.ui.TextInput(
                    label="Beschreibung",
                    placeholder=(
                        "Beschreibe dein "
                        "Anliegen möglichst "
                        "genau."
                    ),
                    style=(
                        discord.TextStyle
                        .paragraph
                    ),
                    max_length=1500,
                ),
            ]

        self.form_fields = fields

        for field in fields:
            self.add_item(field)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        guild = interaction.guild

        if guild is None:
            return

        config = TICKET_TYPES[
            self.ticket_type
        ]

        existing = (
            await find_open_ticket(
                guild,
                interaction.user.id,
                self.ticket_type,
            )
        )

        if existing:

            await (
                interaction.response
                .send_message(
                    (
                        "⚠️ Du hast hier "
                        "bereits ein offenes "
                        f"Ticket: "
                        f"{existing.mention}"
                    ),
                    ephemeral=True,
                )
            )

            return

        category = guild.get_channel(
            config["category_id"]
        )

        staff_role = guild.get_role(
            config["role_id"]
        )

        if not isinstance(
            category,
            discord.CategoryChannel,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Die Ziel-Kategorie "
                        "wurde nicht gefunden."
                    ),
                    ephemeral=True,
                )
            )

            return

        if staff_role is None:

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Die zuständige "
                        "Teamrolle wurde nicht "
                        "gefunden."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        bot_member = guild.me

        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False,
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                ),
        }

        if bot_member:

            overwrites[
                bot_member
            ] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True,
                )
            )

        # WICHTIG:
        # Ticketname kommt vom
        # Discord-Username des Erstellers.
        creator_name = slugify(
            interaction.user.name
        )

        channel_name = (
            f"{self.ticket_type}-"
            f"{creator_name}"
        )[:100]

        try:

            channel = (
                await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=make_topic(
                        ticket_type=(
                            self.ticket_type
                        ),
                        owner_id=(
                            interaction.user.id
                        ),
                        status="open",
                    ),
                    reason=(
                        "EHRP Ticket erstellt "
                        f"von {interaction.user}"
                    ),
                )
            )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Ticket erstellen "
                f"fehlgeschlagen: {error}"
            )

            await (
                interaction.followup.send(
                    (
                        "❌ Das Ticket konnte "
                        "nicht erstellt werden."
                    ),
                    ephemeral=True,
                )
            )

            return

        meta = read_topic(
            channel
        )

        if meta is None:

            await (
                interaction.followup.send(
                    (
                        "❌ Ticket-Metadaten "
                        "konnten nicht erstellt "
                        "werden."
                    ),
                    ephemeral=True,
                )
            )

            return

        embed = (
            await build_ticket_embed(
                channel,
                meta,
                config,
            )
        )

        for field in (
            self.form_fields
        ):

            embed.add_field(
                name=field.label,
                value=(
                    str(field.value)[:1024]
                ),
                inline=False,
            )

        try:

            control = (
                await channel.send(
                    content=(
                        f"{interaction.user.mention} "
                        f"{staff_role.mention}"
                    ),
                    embed=embed,
                    view=OpenTicketView(),
                    allowed_mentions=(
                        discord.AllowedMentions(
                            users=True,
                            roles=True,
                            everyone=False,
                        )
                    ),
                )
            )

            await channel.edit(
                topic=make_topic(
                    ticket_type=(
                        self.ticket_type
                    ),
                    owner_id=(
                        interaction.user.id
                    ),
                    claimed_id=0,
                    control_id=control.id,
                    status="open",
                )
            )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Ticket-Control "
                f"fehlgeschlagen: {error}"
            )

        await send_log(
            guild,
            "🎫 Ticket erstellt",
            (
                f"**Ticket:** "
                f"{channel.mention}\n"
                f"**Bereich:** "
                f"{config['emoji']} "
                f"{config['name']}\n"
                f"**Ersteller:** "
                f"{interaction.user.mention}\n"
                f"**Channelname:** "
                f"`#{channel.name}`"
            ),
            OPEN_COLOR,
        )

        await (
            interaction.followup.send(
                (
                    "✅ Ticket erstellt: "
                    f"{channel.mention}"
                ),
                ephemeral=True,
            )
        )


# ============================================================
# OPEN TICKET CONTROLS
# ============================================================

class OpenTicketView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    async def on_error(
        self,
        interaction,
        error,
        item,
    ):

        print(
            "❌ Ticket-Button Fehler "
            f"[{getattr(item, 'custom_id', '?')}]: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        try:

            if (
                interaction.response
                .is_done()
            ):

                await (
                    interaction.followup
                    .send(
                        (
                            "❌ Die Aktion ist "
                            "fehlgeschlagen. "
                            "Der Fehler wurde "
                            "geloggt."
                        ),
                        ephemeral=True,
                    )
                )

            else:

                await (
                    interaction.response
                    .send_message(
                        (
                            "❌ Die Aktion ist "
                            "fehlgeschlagen. "
                            "Der Fehler wurde "
                            "geloggt."
                        ),
                        ephemeral=True,
                    )
                )

        except discord.HTTPException:
            pass

    @discord.ui.button(
        label="Übernehmen",
        emoji="👤",
        style=(
            discord.ButtonStyle
            .success
        ),
        custom_id=(
            "ehrp:ticket:claim"
        ),
    )
    async def claim(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:

            await (
                interaction.response
                .send_message(
                    "❌ Ungültiges Ticket.",
                    ephemeral=True,
                )
            )

            return

        if not is_staff(
            interaction,
            config,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Du bist für diesen "
                        "Ticketbereich nicht "
                        "zuständig."
                    ),
                    ephemeral=True,
                )
            )

            return

        if meta["claimed_id"]:

            member = (
                await resolve_member(
                    interaction.guild,
                    meta["claimed_id"],
                )
            )

            text = (
                "⚠️ Dieses Ticket wurde "
                "bereits übernommen."
            )

            if member:

                text = (
                    "⚠️ Dieses Ticket wurde "
                    f"bereits von "
                    f"{member.mention} "
                    "übernommen."
                )

            await (
                interaction.response
                .send_message(
                    text,
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        meta["claimed_id"] = (
            interaction.user.id
        )

        await channel.edit(
            topic=make_topic(
                ticket_type=meta["type"],
                owner_id=meta["owner_id"],
                claimed_id=meta["claimed_id"],
                control_id=meta["control_id"],
                status=meta["status"],
            ),
            reason=(
                "EHRP Ticket übernommen "
                f"von {interaction.user}"
            ),
        )

        control = (
            await get_control_message(
                channel,
                meta,
            )
        )

        if control:

            old_embed = (
                control.embeds[0]
                if control.embeds
                else None
            )

            new_embed = (
                await build_ticket_embed(
                    channel,
                    meta,
                    config,
                    previous=old_embed,
                )
            )

            await control.edit(
                embed=new_embed,
                view=OpenTicketView(),
            )

        await send_log(
            interaction.guild,
            "👤 Ticket übernommen",
            (
                f"**Ticket:** "
                f"{channel.mention}\n"
                f"**Bearbeiter:** "
                f"{interaction.user.mention}"
            ),
            CLAIMED_COLOR,
        )

        await (
            interaction.followup.send(
                (
                    "✅ Du hast das Ticket "
                    "übernommen."
                ),
                ephemeral=True,
            )
        )

    @discord.ui.button(
        label="Person hinzufügen",
        emoji="➕",
        style=(
            discord.ButtonStyle.primary
        ),
        custom_id=(
            "ehrp:ticket:add_user"
        ),
    )
    async def add_user(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:
            return

        if not is_staff(
            interaction,
            config,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Nur das zuständige "
                        "Team kann Personen "
                        "hinzufügen."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response
            .send_modal(
                AddUserModal()
            )
        )

    @discord.ui.button(
        label="Schließen",
        emoji="🔒",
        style=(
            discord.ButtonStyle.danger
        ),
        custom_id=(
            "ehrp:ticket:close"
        ),
    )
    async def close(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:
            return

        owner_can_close = (
            interaction.user.id
            == meta["owner_id"]
        )

        if (
            not owner_can_close
            and not is_staff(
                interaction,
                config,
            )
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Du kannst dieses "
                        "Ticket nicht schließen."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response
            .send_modal(
                CloseTicketModal()
            )
        )


# ============================================================
# ADD USER MODAL
# ============================================================

class AddUserModal(
    discord.ui.Modal,
    title="Person hinzufügen",
):

    user = discord.ui.TextInput(
        label="User-ID oder Erwähnung",
        placeholder=(
            "@User oder "
            "123456789012345678"
        ),
        max_length=50,
    )

    async def on_submit(
        self,
        interaction,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        digits = re.sub(
            r"\D",
            "",
            str(self.user.value),
        )

        if not digits:

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Ungültige "
                        "User-ID/Erwähnung."
                    ),
                    ephemeral=True,
                )
            )

            return

        member = (
            await resolve_member(
                interaction.guild,
                int(digits),
            )
        )

        if member is None:

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Diese Person "
                        "wurde nicht gefunden."
                    ),
                    ephemeral=True,
                )
            )

            return

        try:

            await channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                reason=(
                    "EHRP Ticket: "
                    f"hinzugefügt von "
                    f"{interaction.user}"
                ),
            )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Person hinzufügen "
                f"fehlgeschlagen: {error}"
            )

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Die Person konnte "
                        "nicht hinzugefügt "
                        "werden."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response
            .send_message(
                (
                    f"✅ {member.mention} "
                    "wurde hinzugefügt."
                ),
                ephemeral=True,
            )
        )

        await send_log(
            interaction.guild,
            "➕ Person hinzugefügt",
            (
                f"**Ticket:** "
                f"{channel.mention}\n"
                f"**Person:** "
                f"{member.mention}\n"
                f"**Von:** "
                f"{interaction.user.mention}"
            ),
        )


# ============================================================
# CLOSE MODAL
# ============================================================

class CloseTicketModal(
    discord.ui.Modal,
    title="Ticket schließen",
):

    reason = discord.ui.TextInput(
        label="Schließgrund",
        placeholder=(
            "Warum wird das Ticket "
            "geschlossen?"
        ),
        style=(
            discord.TextStyle.paragraph
        ),
        required=False,
        max_length=500,
    )

    async def on_submit(
        self,
        interaction,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:
            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        reason_text = (
            str(self.reason.value).strip()
            or "Kein Grund angegeben"
        )

        meta["status"] = "closed"

        owner = (
            await resolve_member(
                interaction.guild,
                meta["owner_id"],
            )
        )

        if owner:

            try:

                await (
                    channel.set_permissions(
                        owner,
                        view_channel=True,
                        send_messages=False,
                        read_message_history=True,
                        reason=(
                            "EHRP Ticket "
                            "geschlossen"
                        ),
                    )
                )

            except discord.HTTPException:
                pass

        try:

            if not (
                channel.name.startswith(
                    "closed-"
                )
            ):

                await channel.edit(
                    name=(
                        f"closed-"
                        f"{channel.name}"
                    )[:100],
                    reason=(
                        "EHRP Ticket "
                        "geschlossen von "
                        f"{interaction.user}"
                    ),
                )

            await channel.edit(
                topic=make_topic(
                    ticket_type=(
                        meta["type"]
                    ),
                    owner_id=(
                        meta["owner_id"]
                    ),
                    claimed_id=(
                        meta["claimed_id"]
                    ),
                    control_id=(
                        meta["control_id"]
                    ),
                    status="closed",
                )
            )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Ticket schließen "
                f"fehlgeschlagen: {error}"
            )

        control = (
            await get_control_message(
                channel,
                meta,
            )
        )

        if control:

            old_embed = (
                control.embeds[0]
                if control.embeds
                else None
            )

            new_embed = (
                await build_ticket_embed(
                    channel,
                    meta,
                    config,
                    previous=old_embed,
                    close_reason=(
                        reason_text
                    ),
                )
            )

            try:

                await control.edit(
                    embed=new_embed,
                    view=ClosedTicketView(),
                )

            except (
                discord.HTTPException
            ) as error:

                print(
                    "❌ Control-Message "
                    f"Fehler: {error}"
                )

        transcript = (
            await make_transcript(
                channel
            )
        )

        await send_log(
            interaction.guild,
            "🔒 Ticket geschlossen",
            (
                f"**Ticket:** "
                f"`#{channel.name}`\n"
                f"**Ersteller:** "
                f"<@{meta['owner_id']}>\n"
                f"**Geschlossen von:** "
                f"{interaction.user.mention}\n"
                f"**Bereich:** "
                f"{config['emoji']} "
                f"{config['name']}\n"
                f"**Grund:** "
                f"{reason_text}"
            ),
            CLOSED_COLOR,
            transcript,
        )

        await (
            interaction.followup.send(
                (
                    "✅ Ticket wurde "
                    "geschlossen."
                ),
                ephemeral=True,
            )
        )


# ============================================================
# CLOSED CONTROLS
# ============================================================

class ClosedTicketView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Wieder öffnen",
        emoji="🔓",
        style=(
            discord.ButtonStyle.success
        ),
        custom_id=(
            "ehrp:ticket:reopen"
        ),
    )
    async def reopen(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:
            return

        if not is_staff(
            interaction,
            config,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Nur das zuständige "
                        "Team kann das Ticket "
                        "wieder öffnen."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        owner = (
            await resolve_member(
                interaction.guild,
                meta["owner_id"],
            )
        )

        if owner:

            try:

                await (
                    channel.set_permissions(
                        owner,
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        attach_files=True,
                        embed_links=True,
                        reason=(
                            "EHRP Ticket "
                            "wieder geöffnet"
                        ),
                    )
                )

            except discord.HTTPException:
                pass

        if channel.name.startswith(
            "closed-"
        ):

            try:

                await channel.edit(
                    name=(
                        channel.name[7:]
                    ),
                    reason=(
                        "EHRP Ticket "
                        "wieder geöffnet"
                    ),
                )

            except discord.HTTPException:
                pass

        meta["status"] = "open"

        await channel.edit(
            topic=make_topic(
                ticket_type=(
                    meta["type"]
                ),
                owner_id=(
                    meta["owner_id"]
                ),
                claimed_id=(
                    meta["claimed_id"]
                ),
                control_id=(
                    meta["control_id"]
                ),
                status="open",
            )
        )

        control = (
            await get_control_message(
                channel,
                meta,
            )
        )

        if control:

            old_embed = (
                control.embeds[0]
                if control.embeds
                else None
            )

            new_embed = (
                await build_ticket_embed(
                    channel,
                    meta,
                    config,
                    previous=old_embed,
                )
            )

            await control.edit(
                embed=new_embed,
                view=OpenTicketView(),
            )

        await send_log(
            interaction.guild,
            "🔓 Ticket wieder geöffnet",
            (
                f"**Ticket:** "
                f"{channel.mention}\n"
                f"**Von:** "
                f"{interaction.user.mention}"
            ),
            OPEN_COLOR,
        )

        await (
            interaction.followup.send(
                (
                    "✅ Ticket wurde "
                    "wieder geöffnet."
                ),
                ephemeral=True,
            )
        )

    @discord.ui.button(
        label="Löschen",
        emoji="🗑️",
        style=(
            discord.ButtonStyle.danger
        ),
        custom_id=(
            "ehrp:ticket:delete"
        ),
    )
    async def delete(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        meta, config = (
            get_config(channel)
        )

        if not meta or not config:
            return

        if not is_staff(
            interaction,
            config,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Nur das zuständige "
                        "Team kann Tickets "
                        "löschen."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response
            .send_message(
                (
                    "⚠️ **Dieses Ticket "
                    "wirklich endgültig "
                    "löschen?**"
                ),
                view=DeleteConfirmView(
                    interaction.user.id
                ),
                ephemeral=True,
            )
        )


class DeleteConfirmView(
    discord.ui.View
):

    def __init__(
        self,
        owner_id: int,
    ):

        super().__init__(
            timeout=60
        )

        self.owner_id = owner_id

    async def interaction_check(
        self,
        interaction,
    ):

        if (
            interaction.user.id
            != self.owner_id
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Diese Bestätigung "
                        "gehört nicht dir."
                    ),
                    ephemeral=True,
                )
            )

            return False

        return True

    @discord.ui.button(
        label="Endgültig löschen",
        emoji="🗑️",
        style=(
            discord.ButtonStyle.danger
        ),
    )
    async def confirm(
        self,
        interaction,
        button,
    ):

        channel = (
            interaction.channel
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        await send_log(
            interaction.guild,
            "🗑️ Ticket gelöscht",
            (
                f"**Ticket:** "
                f"`#{channel.name}`\n"
                f"**Gelöscht von:** "
                f"{interaction.user.mention}"
            ),
            CLOSED_COLOR,
        )

        try:

            await channel.delete(
                reason=(
                    "EHRP Ticket gelöscht "
                    f"von {interaction.user}"
                )
            )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Ticket löschen "
                f"fehlgeschlagen: {error}"
            )


# ============================================================
# COG
# ============================================================

class Tickets(
    commands.Cog
):

    def __init__(
        self,
        bot,
    ):

        self.bot = bot

    @app_commands.command(
        name="ticket_panel",
        description=(
            "Erstellt oder aktualisiert "
            "das EHRP Service Center."
        ),
    )
    async def ticket_panel(
        self,
        interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        channel = (
            interaction.guild
            .get_channel(
                PANEL_CHANNEL_ID
            )
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):

            await (
                interaction.response
                .send_message(
                    (
                        "❌ Panel-Channel "
                        "wurde nicht gefunden."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.response.defer(
                ephemeral=True
            )
        )

        existing = None

        try:

            async for message in (
                channel.history(
                    limit=50
                )
            ):

                if (
                    self.bot.user
                    and message.author.id
                    == self.bot.user.id
                    and message.embeds
                    and message.embeds[0].title
                    == "EHRP | SERVICE CENTER"
                ):

                    existing = message
                    break

        except discord.HTTPException:
            pass

        try:

            if existing:

                await existing.edit(
                    embed=build_main_panel(),
                    view=TicketPanelView(),
                )

                text = (
                    "✅ Service Center "
                    "aktualisiert."
                )

            else:

                await channel.send(
                    embed=build_main_panel(),
                    view=TicketPanelView(),
                )

                text = (
                    "✅ Service Center "
                    "erstellt."
                )

        except (
            discord.HTTPException
        ) as error:

            print(
                "❌ Ticket-Panel Fehler: "
                f"{error}"
            )

            await (
                interaction.followup.send(
                    (
                        "❌ Das Service Center "
                        "konnte nicht erstellt "
                        "werden."
                    ),
                    ephemeral=True,
                )
            )

            return

        await (
            interaction.followup.send(
                (
                    f"{text}\n"
                    f"📍 {channel.mention}"
                ),
                ephemeral=True,
            )
        )

    @app_commands.command(
        name="ticket_status",
        description=(
            "Zeigt den Status des "
            "EHRP Ticket-Systems."
        ),
    )
    async def ticket_status(
        self,
        interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        total = 0
        open_count = 0
        closed_count = 0

        for config in (
            TICKET_TYPES.values()
        ):

            category = (
                interaction.guild
                .get_channel(
                    config["category_id"]
                )
            )

            if not isinstance(
                category,
                discord.CategoryChannel,
            ):
                continue

            for channel in (
                category.text_channels
            ):

                meta = read_topic(
                    channel
                )

                if not meta:
                    continue

                total += 1

                if (
                    meta["status"]
                    == "closed"
                ):
                    closed_count += 1

                else:
                    open_count += 1

        embed = discord.Embed(
            title=(
                "⚙️ EHRP | "
                "TICKET SYSTEM"
            ),
            description=(
                "🟢 **System:** Online\n"
                "🟢 **Persistent Controls:** "
                "Online\n"
                "🟢 **Routing:** Online\n\n"
                f"🎫 **Tickets insgesamt:** "
                f"{total}\n"
                f"🟢 **Offen:** "
                f"{open_count}\n"
                f"🔴 **Geschlossen:** "
                f"{closed_count}\n"
                f"📂 **Bereiche:** "
                f"{len(TICKET_TYPES)}"
            ),
            color=OPEN_COLOR,
        )

        await (
            interaction.response
            .send_message(
                embed=embed,
                ephemeral=True,
            )
        )


async def setup(
    bot,
):

    # Persistent Views:
    # funktionieren auch
    # nach Bot-/Render-Neustart.
    bot.add_view(
        TicketPanelView()
    )

    bot.add_view(
        OpenTicketView()
    )

    bot.add_view(
        ClosedTicketView()
    )

    await bot.add_cog(
        Tickets(bot)
    )
