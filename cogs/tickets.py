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
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

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

def clean_channel_name(text: str) -> str:
    text = text.lower().strip()
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:30] or "user"


def make_ticket_topic(
    ticket_type: str,
    owner_id: int,
    claimed_id: int = 0,
) -> str:
    return (
        "EHRP_TICKET|"
        f"type={ticket_type}|"
        f"owner={owner_id}|"
        f"claimed={claimed_id}"
    )


def read_ticket_topic(channel: discord.TextChannel):
    topic = channel.topic or ""

    if not topic.startswith("EHRP_TICKET|"):
        return None

    values = {}

    for part in topic.split("|")[1:]:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        values[key] = value

    try:
        return {
            "type": values["type"],
            "owner_id": int(values["owner"]),
            "claimed_id": int(values.get("claimed", "0")),
        }
    except (KeyError, TypeError, ValueError):
        return None


def get_ticket_info(channel: discord.TextChannel):
    metadata = read_ticket_topic(channel)

    if not metadata:
        return None, None

    return metadata, TICKET_TYPES.get(metadata["type"])


def user_is_ticket_staff(
    interaction: discord.Interaction,
    config: dict,
) -> bool:
    if not isinstance(interaction.user, discord.Member):
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    role = interaction.guild.get_role(config["role_id"])

    return role is not None and role in interaction.user.roles


def ticket_number(channel: discord.TextChannel) -> str:
    return str(channel.id)[-6:]


async def get_ticket_owner(
    guild: discord.Guild,
    owner_id: int,
):
    member = guild.get_member(owner_id)

    if member:
        return member

    try:
        return await guild.fetch_member(owner_id)
    except discord.HTTPException:
        return None


async def send_ticket_log(
    guild: discord.Guild,
    title: str,
    description: str,
    color: int = SYSTEM_COLOR,
    file: discord.File | None = None,
):
    log_channel = guild.get_channel(TICKET_LOG_CHANNEL_ID)

    if not isinstance(log_channel, discord.TextChannel):
        print("⚠️ Ticket-Log-Channel nicht gefunden.")
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(
        text="EHRP | System • Ticket Logging"
    )

    try:
        if file is None:
            await log_channel.send(embed=embed)
        else:
            await log_channel.send(
                embed=embed,
                file=file,
            )

    except discord.HTTPException as error:
        print(
            f"❌ Ticket-Log Fehler: {error}"
        )


async def create_transcript(
    channel: discord.TextChannel,
):
    rows = [
        "EHRP | SYSTEM — TICKET TRANSCRIPT",
        f"Ticket: #{channel.name}",
        f"Channel-ID: {channel.id}",
        "",
        "=" * 55,
        "",
    ]

    try:
        async for message in channel.history(
            limit=1000,
            oldest_first=True,
        ):
            timestamp = message.created_at.strftime(
                "%d.%m.%Y %H:%M:%S UTC"
            )

            content = message.content or ""

            if message.attachments:
                urls = " | ".join(
                    attachment.url
                    for attachment in message.attachments
                )

                content = (
                    f"{content} | Anhänge: {urls}"
                    if content
                    else f"Anhänge: {urls}"
                )

            if not content and message.embeds:
                content = "[Embed / System-Nachricht]"

            if not content:
                content = "[Keine Textnachricht]"

            rows.append(
                f"[{timestamp}] "
                f"{message.author} ({message.author.id}): "
                f"{content}"
            )

    except discord.HTTPException as error:
        print(
            f"❌ Transcript Fehler: {error}"
        )
        return None

    data = "\n".join(rows).encode("utf-8")

    return discord.File(
        io.BytesIO(data),
        filename=f"{channel.name}-transcript.txt",
    )


async def find_existing_ticket(
    guild: discord.Guild,
    user_id: int,
    ticket_type: str,
):
    config = TICKET_TYPES[ticket_type]

    category = guild.get_channel(
        config["category_id"]
    )

    if not isinstance(
        category,
        discord.CategoryChannel,
    ):
        return None

    for channel in category.text_channels:
        metadata = read_ticket_topic(channel)

        if not metadata:
            continue

        if (
            metadata["owner_id"] == user_id
            and metadata["type"] == ticket_type
            and not channel.name.startswith("closed-")
        ):
            return channel

    return None


async def build_ticket_embed(
    channel: discord.TextChannel,
    status: str,
    form_fields: list[tuple[str, str]] | None = None,
):
    metadata, config = get_ticket_info(channel)

    if not metadata or not config:
        return None

    owner = await get_ticket_owner(
        channel.guild,
        metadata["owner_id"],
    )

    claimer = (
        channel.guild.get_member(
            metadata["claimed_id"]
        )
        if metadata["claimed_id"]
        else None
    )

    role = channel.guild.get_role(
        config["role_id"]
    )

    if status == "claimed":
        status_text = "🟡 In Bearbeitung"
        color = WARNING_COLOR

    elif status == "closed":
        status_text = "🔴 Geschlossen"
        color = ERROR_COLOR

    else:
        status_text = "🟢 Offen"
        color = SUCCESS_COLOR

    owner_text = (
        owner.mention
        if owner
        else f"<@{metadata['owner_id']}>"
    )

    role_text = (
        role.mention
        if role
        else "Nicht gefunden"
    )

    claimer_text = (
        claimer.mention
        if claimer
        else "Nicht übernommen"
    )

    embed = discord.Embed(
        title=(
            f"{config['emoji']} EHRP | "
            f"TICKET #{ticket_number(channel)}"
        ),
        description=(
            "### SERVICE SESSION\n\n"
            f"**Status:** {status_text}\n"
            f"**Bereich:** "
            f"{config['emoji']} {config['name']}\n"
            f"**Ersteller:** {owner_text}\n"
            f"**Zuständig:** {role_text}\n"
            f"**Bearbeiter:** {claimer_text}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    if owner:
        embed.set_thumbnail(
            url=owner.display_avatar.url
        )

        embed.set_author(
            name=owner.display_name,
            icon_url=owner.display_avatar.url,
        )

    for label, value in form_fields or []:
        embed.add_field(
            name=label,
            value=value[:1024],
            inline=False,
        )

    embed.set_footer(
        text="EHRP | System • Ticket Control"
    )

    return embed


# ============================================================
# MAIN PANEL
# ============================================================

def build_main_panel():
    embed = discord.Embed(
        title="EHRP | SERVICE CENTER",
        description=(
            "### DIGITAL SERVICE PORTAL\n\n"
            "Willkommen im zentralen Service Center "
            "von **EHRP/VC**.\n"
            "Wähle unten den Bereich aus, "
            "der zu deinem Anliegen passt.\n\n"
            "🟢 **System online**\n"
            "🔒 **Private Tickets**\n"
            "⚡ **Automatische Weiterleitung**\n"
            "🛡️ **Internes Logging**\n\n"
            "**Wähle unten deine Abteilung aus.**"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_author(
        name="EHRP | SYSTEM"
    )

    embed.set_footer(
        text="EHRP | System • Service Portal"
    )

    return embed


# ============================================================
# TICKET SELECT
# ============================================================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=config["name"],
                value=key,
                emoji=config["emoji"],
                description=config["description"][:100],
            )
            for key, config in TICKET_TYPES.items()
        ]

        super().__init__(
            placeholder="Abteilung auswählen …",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ehrp:ticket:type_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        try:
            await interaction.response.send_modal(
                TicketCreateModal(
                    self.values[0]
                )
            )

        except Exception as error:
            print(
                f"❌ Ticket Select Fehler: {error}"
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Das Ticketformular "
                    "konnte nicht geöffnet werden.",
                    ephemeral=True,
                )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            TicketSelect()
        )


# ============================================================
# CREATE MODAL
# ============================================================

class TicketCreateModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        self.ticket_type = ticket_type

        config = TICKET_TYPES[ticket_type]

        super().__init__(
            title=f"{config['name']} • Ticket"
        )

        if ticket_type == "entbannung":
            fields = [
                discord.ui.TextInput(
                    label="Ingame-Name",
                    placeholder="Dein RP-/Ingame-Name",
                    max_length=100,
                ),

                discord.ui.TextInput(
                    label="Banngrund",
                    placeholder="Warum wurdest du gebannt?",
                    style=discord.TextStyle.paragraph,
                    max_length=700,
                ),

                discord.ui.TextInput(
                    label="Entbannungsbegründung",
                    placeholder=(
                        "Warum sollten wir dich entbannen?"
                    ),
                    style=discord.TextStyle.paragraph,
                    max_length=1200,
                ),
            ]

        elif ticket_type == "developer":
            fields = [
                discord.ui.TextInput(
                    label="Fehler / System",
                    placeholder="Was funktioniert nicht?",
                    max_length=150,
                ),

                discord.ui.TextInput(
                    label="Beschreibung",
                    placeholder=(
                        "Beschreibe den Fehler "
                        "möglichst genau."
                    ),
                    style=discord.TextStyle.paragraph,
                    max_length=1500,
                ),
            ]

        elif ticket_type == "immobilien":
            fields = [
                discord.ui.TextInput(
                    label="Immobilie / Ort",
                    placeholder=(
                        "Welche Immobilie betrifft "
                        "das Anliegen?"
                    ),
                    max_length=150,
                ),

                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder="Beschreibe dein Anliegen.",
                    style=discord.TextStyle.paragraph,
                    max_length=1500,
                ),
            ]

        elif ticket_type == "socialmedia":
            fields = [
                discord.ui.TextInput(
                    label="Plattform / Thema",
                    placeholder=(
                        "TikTok, YouTube, Instagram, "
                        "Kooperation …"
                    ),
                    max_length=150,
                ),

                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder="Beschreibe dein Anliegen.",
                    style=discord.TextStyle.paragraph,
                    max_length=1500,
                ),
            ]

        elif ticket_type == "fraktion":
            fields = [
                discord.ui.TextInput(
                    label="Fraktion",
                    placeholder=(
                        "Welche Fraktion betrifft "
                        "dein Anliegen?"
                    ),
                    max_length=150,
                ),

                discord.ui.TextInput(
                    label="Anliegen",
                    placeholder="Beschreibe dein Anliegen.",
                    style=discord.TextStyle.paragraph,
                    max_length=1500,
                ),
            ]

        else:
            fields = [
                discord.ui.TextInput(
                    label="Betreff",
                    placeholder="Worum geht es?",
                    max_length=150,
                ),

                discord.ui.TextInput(
                    label="Beschreibung",
                    placeholder=(
                        "Beschreibe dein Anliegen "
                        "möglichst genau."
                    ),
                    style=discord.TextStyle.paragraph,
                    max_length=1500,
                ),
            ]

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

        existing = await find_existing_ticket(
            guild,
            interaction.user.id,
            self.ticket_type,
        )

        if existing:
            await interaction.response.send_message(
                (
                    "⚠️ Du hast in diesem Bereich "
                    "bereits ein offenes Ticket: "
                    f"{existing.mention}"
                ),
                ephemeral=True,
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
            await interaction.response.send_message(
                "❌ Die Ziel-Kategorie "
                "wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        if staff_role is None:
            await interaction.response.send_message(
                "❌ Die zuständige Teamrolle "
                "wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

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

        if guild.me:
            overwrites[guild.me] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_message_history=True,
                )
            )

        try:
            channel = await guild.create_text_channel(
                name=(
                    "ticket-"
                    f"{clean_channel_name(interaction.user.display_name)}"
                ),
                category=category,
                overwrites=overwrites,
                topic=make_ticket_topic(
                    self.ticket_type,
                    interaction.user.id,
                    0,
                ),
                reason=(
                    "EHRP Ticket erstellt von "
                    f"{interaction.user}"
                ),
            )

        except discord.HTTPException as error:
            print(
                f"❌ Ticket Create Fehler: {error}"
            )

            await interaction.followup.send(
                "❌ Das Ticket konnte "
                "nicht erstellt werden.",
                ephemeral=True,
            )
            return

        try:
            await channel.edit(
                name=(
                    f"ticket-"
                    f"{clean_channel_name(config['name'])}-"
                    f"{ticket_number(channel)}"
                )[:100]
            )

        except discord.HTTPException:
            pass

        form_fields = [
            (
                item.label,
                str(item.value),
            )
            for item in self.children
            if isinstance(
                item,
                discord.ui.TextInput,
            )
        ]

        embed = await build_ticket_embed(
            channel,
            "open",
            form_fields,
        )

        try:
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
                    )
                ),
            )

        except discord.HTTPException as error:
            print(
                f"❌ Ticket Message Fehler: {error}"
            )

        await send_ticket_log(
            guild,
            "🎫 Ticket erstellt",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Ticket-ID:** "
                f"`{ticket_number(channel)}`\n"
                f"**Bereich:** "
                f"{config['emoji']} {config['name']}\n"
                f"**Ersteller:** "
                f"{interaction.user.mention}\n"
                f"**Zuständig:** "
                f"{staff_role.mention}"
            ),
            SUCCESS_COLOR,
        )

        await interaction.followup.send(
            (
                "✅ **Ticket erfolgreich erstellt**\n\n"
                f"➡️ {channel.mention}"
            ),
            ephemeral=True,
        )


# ============================================================
# OPEN TICKET CONTROLS
# ============================================================

class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(
        self,
        interaction,
        error,
        item,
    ):
        print(
            "❌ Ticket Button Fehler "
            f"[{getattr(item, 'custom_id', 'unknown')}]: "
            f"{error}"
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ Bei dieser Aktion "
                    "ist ein Fehler aufgetreten.",
                    ephemeral=True,
                )

            else:
                await interaction.response.send_message(
                    "❌ Bei dieser Aktion "
                    "ist ein Fehler aufgetreten.",
                    ephemeral=True,
                )

        except discord.HTTPException:
            pass

    @discord.ui.button(
        label="Übernehmen",
        emoji="👤",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:ticket:claim",
    )
    async def claim(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        # Ersteller darf eigenes Ticket NICHT übernehmen
        if (
            interaction.user.id
            == metadata["owner_id"]
        ):
            await interaction.response.send_message(
                "❌ Du kannst dein eigenes Ticket "
                "nicht übernehmen.",
                ephemeral=True,
            )
            return

        if not user_is_ticket_staff(
            interaction,
            config,
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann "
                "dieses Ticket übernehmen.",
                ephemeral=True,
            )
            return

        if metadata["claimed_id"]:
            current = (
                interaction.guild.get_member(
                    metadata["claimed_id"]
                )
            )

            await interaction.response.send_message(
                (
                    "⚠️ Dieses Ticket wurde bereits von "
                    f"{current.mention if current else 'einem Teammitglied'} "
                    "übernommen."
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        await channel.edit(
            topic=make_ticket_topic(
                metadata["type"],
                metadata["owner_id"],
                interaction.user.id,
            ),
            reason="EHRP Ticket übernommen",
        )

        embed = await build_ticket_embed(
            channel,
            "claimed",
        )

        await interaction.message.edit(
            embed=embed,
            view=self,
        )

        await send_ticket_log(
            interaction.guild,
            "👤 Ticket übernommen",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Bearbeiter:** "
                f"{interaction.user.mention}"
            ),
            WARNING_COLOR,
        )

        await interaction.followup.send(
            "✅ Du hast das Ticket übernommen.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Person hinzufügen",
        emoji="➕",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:ticket:add_user",
    )
    async def add_user(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        # NUR Team darf Personen hinzufügen
        if not user_is_ticket_staff(
            interaction,
            config,
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann "
                "Personen hinzufügen.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            (
                "👥 **Mitglied auswählen**\n"
                "Wähle die Person aus, die Zugriff "
                "auf dieses Ticket bekommen soll."
            ),
            view=TicketMemberSelectView(),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Schließen",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:ticket:close",
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        is_owner = (
            interaction.user.id
            == metadata["owner_id"]
        )

        is_staff = user_is_ticket_staff(
            interaction,
            config,
        )

        if not is_owner and not is_staff:
            await interaction.response.send_message(
                "❌ Du darfst dieses Ticket "
                "nicht schließen.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            CloseTicketModal(
                interaction.message.id
            )
        )


# ============================================================
# MEMBER SELECT — ONLY TEAM
# ============================================================

class TicketMemberSelect(
    discord.ui.UserSelect
):
    def __init__(self):
        super().__init__(
            placeholder="Mitglied auswählen …",
            min_values=1,
            max_values=1,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        if not user_is_ticket_staff(
            interaction,
            config,
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team darf "
                "Personen hinzufügen.",
                ephemeral=True,
            )
            return

        selected = self.values[0]

        member = interaction.guild.get_member(
            selected.id
        )

        if member is None:
            try:
                member = (
                    await interaction.guild.fetch_member(
                        selected.id
                    )
                )

            except discord.HTTPException:
                member = None

        if member is None:
            await interaction.response.send_message(
                "❌ Dieses Mitglied konnte "
                "nicht gefunden werden.",
                ephemeral=True,
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
            )

        except discord.HTTPException as error:
            print(
                "❌ Mitglied hinzufügen Fehler: "
                f"{error}"
            )

            await interaction.response.send_message(
                "❌ Das Mitglied konnte "
                "nicht hinzugefügt werden.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=(
                f"✅ {member.mention} wurde dem "
                "Ticket hinzugefügt."
            ),
            view=None,
        )

        await send_ticket_log(
            interaction.guild,
            "➕ Person hinzugefügt",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Person:** {member.mention}\n"
                f"**Hinzugefügt von:** "
                f"{interaction.user.mention}"
            ),
            SYSTEM_COLOR,
        )


class TicketMemberSelectView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(timeout=60)

        self.add_item(
            TicketMemberSelect()
        )


# ============================================================
# CLOSE MODAL
# ============================================================

class CloseTicketModal(discord.ui.Modal):
    def __init__(
        self,
        ticket_message_id: int,
    ):
        super().__init__(
            title="Ticket schließen"
        )

        self.ticket_message_id = (
            ticket_message_id
        )

        self.reason = discord.ui.TextInput(
            label="Grund",
            placeholder=(
                "Warum wird das Ticket geschlossen?"
            ),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        )

        self.add_item(
            self.reason
        )

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        is_owner = (
            interaction.user.id
            == metadata["owner_id"]
        )

        is_staff = user_is_ticket_staff(
            interaction,
            config,
        )

        if not is_owner and not is_staff:
            await interaction.response.send_message(
                "❌ Du darfst dieses Ticket "
                "nicht schließen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        owner = await get_ticket_owner(
            interaction.guild,
            metadata["owner_id"],
        )

        reason_text = (
            str(self.reason.value).strip()
            or "Kein Grund angegeben"
        )

        if owner:
            try:
                await channel.set_permissions(
                    owner,
                    view_channel=True,
                    send_messages=False,
                    read_message_history=True,
                )

            except discord.HTTPException:
                pass

        transcript = await create_transcript(
            channel
        )

        old_name = channel.name

        if not channel.name.startswith(
            "closed-"
        ):
            try:
                await channel.edit(
                    name=(
                        f"closed-{channel.name}"
                    )[:100],
                    reason="EHRP Ticket geschlossen",
                )

            except discord.HTTPException as error:
                print(
                    "❌ Ticket Rename Fehler: "
                    f"{error}"
                )

        await send_ticket_log(
            interaction.guild,
            "🔒 Ticket geschlossen",
            (
                f"**Ticket:** `#{old_name}`\n"
                f"**Ersteller:** "
                f"<@{metadata['owner_id']}>\n"
                f"**Geschlossen von:** "
                f"{interaction.user.mention}\n"
                f"**Bereich:** "
                f"{config['emoji']} {config['name']}\n"
                f"**Grund:** {reason_text}"
            ),
            ERROR_COLOR,
            transcript,
        )

        embed = await build_ticket_embed(
            channel,
            "closed",
        )

        if embed:
            embed.add_field(
                name="Schließung",
                value=(
                    f"**Geschlossen von:** "
                    f"{interaction.user.mention}\n"
                    f"**Grund:** {reason_text}"
                ),
                inline=False,
            )

        try:
            ticket_message = (
                await channel.fetch_message(
                    self.ticket_message_id
                )
            )

            await ticket_message.edit(
                embed=embed,
                view=ClosedTicketView(),
            )

        except discord.HTTPException as error:
            print(
                "❌ Ticket Message Close Fehler: "
                f"{error}"
            )

        await interaction.followup.send(
            "✅ Ticket wurde erfolgreich geschlossen.",
            ephemeral=True,
        )


# ============================================================
# CLOSED TICKET CONTROLS
# ============================================================

class ClosedTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Wieder öffnen",
        emoji="🔓",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:ticket:reopen",
    )
    async def reopen(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        if not user_is_ticket_staff(
            interaction,
            config,
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann "
                "das Ticket wieder öffnen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        owner = await get_ticket_owner(
            interaction.guild,
            metadata["owner_id"],
        )

        if owner:
            try:
                await channel.set_permissions(
                    owner,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                )

            except discord.HTTPException:
                pass

        if channel.name.startswith(
            "closed-"
        ):
            try:
                await channel.edit(
                    name=channel.name[7:],
                    reason=(
                        "EHRP Ticket wieder geöffnet"
                    ),
                )

            except discord.HTTPException:
                pass

        status = (
            "claimed"
            if metadata["claimed_id"]
            else "open"
        )

        embed = await build_ticket_embed(
            channel,
            status,
        )

        await interaction.message.edit(
            embed=embed,
            view=OpenTicketView(),
        )

        await send_ticket_log(
            interaction.guild,
            "🔓 Ticket wieder geöffnet",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Geöffnet von:** "
                f"{interaction.user.mention}"
            ),
            SUCCESS_COLOR,
        )

        await interaction.followup.send(
            "✅ Ticket wurde wieder geöffnet.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Löschen",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:ticket:delete",
    )
    async def delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        metadata, config = get_ticket_info(
            channel
        )

        if not metadata or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        if not user_is_ticket_staff(
            interaction,
            config,
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann "
                "ein Ticket löschen.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            (
                "⚠️ **Ticket endgültig löschen?**\n"
                "Diese Aktion kann nicht "
                "rückgängig gemacht werden."
            ),
            view=DeleteConfirmView(),
            ephemeral=True,
        )


class DeleteConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Endgültig löschen",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        await send_ticket_log(
            interaction.guild,
            "🗑️ Ticket gelöscht",
            (
                f"**Ticket:** `#{channel.name}`\n"
                f"**Gelöscht von:** "
                f"{interaction.user.mention}"
            ),
            ERROR_COLOR,
        )

        try:
            await channel.delete(
                reason=(
                    "EHRP Ticket gelöscht von "
                    f"{interaction.user}"
                )
            )

        except discord.HTTPException as error:
            print(
                f"❌ Ticket Delete Fehler: {error}"
            )


# ============================================================
# COG
# ============================================================

class Tickets(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        bot.add_view(
            TicketPanelView()
        )

        bot.add_view(
            OpenTicketView()
        )

        bot.add_view(
            ClosedTicketView()
        )

    @app_commands.command(
        name="ticket_panel",
        description=(
            "Erstellt oder aktualisiert "
            "das EHRP Service Center."
        ),
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        channel = (
            interaction.guild.get_channel(
                PANEL_CHANNEL_ID
            )
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Panel-Channel wurde "
                "nicht gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        existing_message = None

        try:
            async for message in channel.history(
                limit=50
            ):
                if (
                    message.author.id
                    == self.bot.user.id
                    and message.embeds
                    and message.embeds[0].title
                    == "EHRP | SERVICE CENTER"
                ):
                    existing_message = message
                    break

        except discord.HTTPException:
            pass

        try:
            if existing_message:
                await existing_message.edit(
                    embed=build_main_panel(),
                    view=TicketPanelView(),
                )

                result_text = (
                    "✅ **Service Center aktualisiert**"
                )

            else:
                await channel.send(
                    embed=build_main_panel(),
                    view=TicketPanelView(),
                )

                result_text = (
                    "✅ **Service Center erstellt**"
                )

        except discord.HTTPException as error:
            print(
                f"❌ Ticket Panel Fehler: {error}"
            )

            await interaction.followup.send(
                "❌ Das Service Center konnte "
                "nicht erstellt werden.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            (
                f"{result_text}\n\n"
                f"📍 {channel.mention}"
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="ticket_status",
        description=(
            "Zeigt den Status des Ticket-Systems."
        ),
    )
    async def ticket_status(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        total = 0
        open_count = 0
        closed_count = 0

        for config in TICKET_TYPES.values():
            category = (
                interaction.guild.get_channel(
                    config["category_id"]
                )
            )

            if not isinstance(
                category,
                discord.CategoryChannel,
            ):
                continue

            for channel in category.text_channels:
                if not read_ticket_topic(channel):
                    continue

                total += 1

                if channel.name.startswith(
                    "closed-"
                ):
                    closed_count += 1

                else:
                    open_count += 1

        embed = discord.Embed(
            title="⚙️ EHRP | TICKET SYSTEM",
            description=(
                "🟢 **System:** Online\n"
                "🟢 **Persistent Controls:** Online\n"
                "🟢 **Routing:** Online\n\n"
                f"🎫 **Tickets insgesamt:** {total}\n"
                f"🟢 **Offen:** {open_count}\n"
                f"🔴 **Geschlossen:** {closed_count}\n"
                f"📂 **Bereiche:** "
                f"{len(TICKET_TYPES)}"
            ),
            color=SUCCESS_COLOR,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        Tickets(bot)
    )
