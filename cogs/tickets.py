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
        "description": "Allgemeine Fragen, Probleme und Support.",
        "category_id": 1526938849618432000,
        "role_id": 1526956922555732151,
    },

    "entbannung": {
        "name": "Entbannung",
        "emoji": "🔓",
        "description": "Stelle einen Antrag auf Entbannung.",
        "category_id": 1526938782732124201,
        "role_id": 1526955621981753435,
    },

    "immobilien": {
        "name": "Immobilien",
        "emoji": "🏠",
        "description": "Anfragen zu Häusern, Wohnungen und Grundstücken.",
        "category_id": 1526938582772875404,
        "role_id": 1526956922555732151,
    },

    "socialmedia": {
        "name": "Social Media",
        "emoji": "📱",
        "description": "Social Media, Content und Medienanfragen.",
        "category_id": 1526938931013222570,
        "role_id": 1526956524466081802,
    },

    "developer": {
        "name": "Developer",
        "emoji": "💻",
        "description": "Bugs, technische Probleme und Development.",
        "category_id": 1526980142054903969,
        "role_id": 1526955429697949706,
    },

    "fraktion": {
        "name": "Fraktion",
        "emoji": "🏛️",
        "description": "Anliegen rund um Fraktionen.",
        "category_id": 1526982043009941564,
        "role_id": 1532505422752383048,
    },
}


# ============================================================
# HELPER
# ============================================================

def safe_channel_name(text: str) -> str:
    text = text.lower()
    text = text.replace("ä", "ae")
    text = text.replace("ö", "oe")
    text = text.replace("ü", "ue")
    text = text.replace("ß", "ss")

    text = re.sub(r"[^a-z0-9\-]", "-", text)
    text = re.sub(r"-+", "-", text)

    return text.strip("-")[:35]


def build_topic(
    ticket_type: str,
    owner_id: int,
    claimed_id: int = 0,
) -> str:

    return (
        f"EHRP_TICKET|"
        f"type={ticket_type}|"
        f"owner={owner_id}|"
        f"claimed={claimed_id}"
    )


def read_topic(channel: discord.TextChannel):

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

    except (KeyError, ValueError):
        return None


def get_ticket_config(
    channel: discord.TextChannel,
):

    data = read_topic(channel)

    if not data:
        return None, None

    config = TICKET_TYPES.get(
        data["type"]
    )

    return data, config


def is_ticket_staff(
    member: discord.Member,
    role: discord.Role | None,
) -> bool:

    if member.guild_permissions.administrator:
        return True

    if role and role in member.roles:
        return True

    return False


async def send_ticket_log(
    guild: discord.Guild,
    title: str,
    description: str,
    color: int = SYSTEM_COLOR,
    file: discord.File | None = None,
):

    log_channel = guild.get_channel(
        TICKET_LOG_CHANNEL_ID
    )

    if not isinstance(
        log_channel,
        discord.TextChannel,
    ):
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_footer(
        text="EHRP | System • Ticket Logs"
    )

    try:

        if file:

            await log_channel.send(
                embed=embed,
                file=file,
            )

        else:

            await log_channel.send(
                embed=embed
            )

    except discord.HTTPException:
        pass


async def create_transcript(
    channel: discord.TextChannel,
):

    lines = [
        "EHRP | SYSTEM",
        "TICKET TRANSCRIPT",
        "",
        f"Channel: {channel.name}",
        f"Channel ID: {channel.id}",
        "",
        "========================================",
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

                attachments = " ".join(
                    attachment.url
                    for attachment in message.attachments
                )

                content += (
                    f" [Attachments: {attachments}]"
                )

            if not content and message.embeds:
                content = "[Embed]"

            lines.append(
                f"[{timestamp}] "
                f"{message.author} "
                f"({message.author.id}): "
                f"{content}"
            )

    except discord.HTTPException:
        return None

    transcript = "\n".join(lines)

    data = io.BytesIO(
        transcript.encode("utf-8")
    )

    return discord.File(
        data,
        filename=f"{channel.name}-transcript.txt",
    )


async def find_open_ticket(
    guild: discord.Guild,
    owner_id: int,
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

        data = read_topic(channel)

        if not data:
            continue

        if (
            data["owner_id"] == owner_id
            and data["type"] == ticket_type
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
            "## Willkommen im Service Center\n"
            "Hier kannst du dein Anliegen direkt an die "
            "zuständige Abteilung weiterleiten.\n\n"

            "**SYSTEM STATUS**\n"
            "🟢 Service Center Online\n"
            "🟢 Ticket Routing Aktiv\n"
            "🟢 Private Sessions Aktiv\n\n"

            "**SO FUNKTIONIERT ES**\n"
            "Wähle unten den passenden Bereich aus.\n"
            "Anschließend öffnet sich ein Formular.\n"
            "Danach erstellt das System automatisch "
            "dein privates Ticket.\n\n"

            "🔒 Nur du und die zuständige Abteilung sehen dein Ticket.\n"
            "⚡ Automatische Weiterleitung\n"
            "📑 Interne Ticket-Dokumentation"
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

        options = []

        for key, data in TICKET_TYPES.items():

            options.append(
                discord.SelectOption(
                    label=data["name"],
                    value=key,
                    emoji=data["emoji"],
                    description=data["description"][:100],
                )
            )

        super().__init__(
            placeholder="Ticket-Bereich auswählen …",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ehrp_ticket_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):

        ticket_type = self.values[0]

        await interaction.response.send_modal(
            TicketModal(ticket_type)
        )


class TicketPanelView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


# ============================================================
# TICKET MODAL
# ============================================================

class TicketModal(discord.ui.Modal):

    def __init__(
        self,
        ticket_type: str,
    ):

        self.ticket_type = ticket_type

        config = TICKET_TYPES[
            ticket_type
        ]

        super().__init__(
            title=(
                f"{config['emoji']} "
                f"{config['name']}"
            )
        )

        # ----------------------------------------
        # ENTBANNUNG
        # ----------------------------------------

        if ticket_type == "entbannung":

            self.field1 = discord.ui.TextInput(
                label="Ingame-Name",
                placeholder="Dein Name im RP",
                max_length=100,
            )

            self.field2 = discord.ui.TextInput(
                label="Banngrund",
                placeholder="Warum wurdest du gebannt?",
                style=discord.TextStyle.paragraph,
                max_length=500,
            )

            self.field3 = discord.ui.TextInput(
                label="Warum solltest du entbannt werden?",
                placeholder="Begründe deinen Antrag.",
                style=discord.TextStyle.paragraph,
                max_length=1000,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)
            self.add_item(self.field3)

        # ----------------------------------------
        # DEVELOPER
        # ----------------------------------------

        elif ticket_type == "developer":

            self.field1 = discord.ui.TextInput(
                label="Problem / System",
                placeholder="Was funktioniert nicht?",
                max_length=150,
            )

            self.field2 = discord.ui.TextInput(
                label="Fehlerbeschreibung",
                placeholder=(
                    "Beschreibe genau, "
                    "was passiert ist."
                ),
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)

        # ----------------------------------------
        # IMMOBILIEN
        # ----------------------------------------

        elif ticket_type == "immobilien":

            self.field1 = discord.ui.TextInput(
                label="Immobilie / Standort",
                placeholder="Um welche Immobilie geht es?",
                max_length=150,
            )

            self.field2 = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)

        # ----------------------------------------
        # FRAKTION
        # ----------------------------------------

        elif ticket_type == "fraktion":

            self.field1 = discord.ui.TextInput(
                label="Fraktion",
                placeholder="Welche Fraktion?",
                max_length=150,
            )

            self.field2 = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)

        # ----------------------------------------
        # SOCIAL MEDIA
        # ----------------------------------------

        elif ticket_type == "socialmedia":

            self.field1 = discord.ui.TextInput(
                label="Plattform / Thema",
                placeholder=(
                    "TikTok, Instagram, "
                    "YouTube, Kooperation …"
                ),
                max_length=150,
            )

            self.field2 = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)

        # ----------------------------------------
        # HIGH TEAM / ALLGEMEIN
        # ----------------------------------------

        else:

            self.field1 = discord.ui.TextInput(
                label="Betreff",
                placeholder="Worum geht es?",
                max_length=150,
            )

            self.field2 = discord.ui.TextInput(
                label="Beschreibung",
                placeholder=(
                    "Beschreibe dein Anliegen "
                    "möglichst genau."
                ),
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field1)
            self.add_item(self.field2)

    # ========================================================
    # MODAL SUBMIT
    # ========================================================

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

        existing = await find_open_ticket(
            guild,
            interaction.user.id,
            self.ticket_type,
        )

        if existing:

            await interaction.response.send_message(
                (
                    "⚠️ Du hast in diesem Bereich bereits "
                    f"ein Ticket:\n{existing.mention}"
                ),
                ephemeral=True,
            )

            return

        category = guild.get_channel(
            config["category_id"]
        )

        support_role = guild.get_role(
            config["role_id"]
        )

        if not isinstance(
            category,
            discord.CategoryChannel,
        ):

            await interaction.response.send_message(
                "❌ Ticket-Kategorie nicht gefunden.",
                ephemeral=True,
            )

            return

        if support_role is None:

            await interaction.response.send_message(
                "❌ Zuständige Teamrolle nicht gefunden.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
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

            support_role:
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
            ] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
            )

        user_name = safe_channel_name(
            interaction.user.display_name
        )

        try:

            channel = await guild.create_text_channel(
                name=(
                    f"ticket-{user_name}"
                ),
                category=category,
                overwrites=overwrites,
                topic=build_topic(
                    self.ticket_type,
                    interaction.user.id,
                ),
                reason=(
                    f"Ticket erstellt von "
                    f"{interaction.user}"
                ),
            )

        except discord.HTTPException as error:

            await interaction.followup.send(
                (
                    "❌ Ticket konnte nicht "
                    f"erstellt werden.\n`{error}`"
                ),
                ephemeral=True,
            )

            return

        ticket_number = str(
            channel.id
        )[-6:]

        try:

            await channel.edit(
                name=(
                    f"ticket-{ticket_number}"
                )
            )

        except discord.HTTPException:
            pass

        fields = []

        for item in self.children:

            if isinstance(
                item,
                discord.ui.TextInput,
            ):

                fields.append(
                    (
                        item.label,
                        str(item.value),
                    )
                )

        embed = discord.Embed(
            title=(
                f"{config['emoji']} "
                f"EHRP | TICKET #{ticket_number}"
            ),
            description=(
                "## Ticket erstellt\n\n"
                "🟢 **Status:** Offen\n"
                f"📂 **Bereich:** {config['name']}\n"
                f"👤 **Ersteller:** {interaction.user.mention}\n"
                f"🛡️ **Zuständig:** {support_role.mention}\n"
                "👨‍💼 **Bearbeiter:** Nicht übernommen\n\n"
                "Ein Teammitglied wird sich "
                "so schnell wie möglich melden."
            ),
            color=SYSTEM_COLOR,
            timestamp=datetime.now(timezone.utc),
        )

        for label, value in fields:

            embed.add_field(
                name=label,
                value=value[:1024],
                inline=False,
            )

        embed.set_footer(
            text="EHRP | System • Ticket Control"
        )

        await channel.send(
            content=(
                f"{interaction.user.mention} "
                f"{support_role.mention}"
            ),
            embed=embed,
            view=OpenTicketView(),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=True,
            ),
        )

        await send_ticket_log(
            guild,
            "🎫 Ticket erstellt",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Ticket-ID:** `{ticket_number}`\n"
                f"**Bereich:** {config['emoji']} {config['name']}\n"
                f"**Ersteller:** {interaction.user.mention}\n"
                f"**Zuständige Rolle:** {support_role.mention}"
            ),
        )

        await interaction.followup.send(
            (
                "✅ **Ticket erfolgreich erstellt**\n\n"
                f"{channel.mention}"
            ),
            ephemeral=True,
        )


# ============================================================
# OPEN TICKET VIEW
# ============================================================

class OpenTicketView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    # --------------------------------------------------------
    # CLAIM
    # --------------------------------------------------------

    @discord.ui.button(
        label="Übernehmen",
        emoji="👤",
        style=discord.ButtonStyle.success,
        custom_id="ehrp_ticket_claim",
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

        data, config = get_ticket_config(
            channel
        )

        if not data or not config:

            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )

            return

        role = interaction.guild.get_role(
            config["role_id"]
        )

        if not is_ticket_staff(
            interaction.user,
            role,
        ):

            await interaction.response.send_message(
                "❌ Du bist für dieses Ticket nicht zuständig.",
                ephemeral=True,
            )

            return

        if data["claimed_id"]:

            member = interaction.guild.get_member(
                data["claimed_id"]
            )

            await interaction.response.send_message(
                (
                    "⚠️ Dieses Ticket wurde bereits "
                    "übernommen von "
                    f"{member.mention if member else 'einem Teammitglied'}."
                ),
                ephemeral=True,
            )

            return

        await channel.edit(
            topic=build_topic(
                data["type"],
                data["owner_id"],
                interaction.user.id,
            )
        )

        if interaction.message.embeds:

            embed = discord.Embed.from_dict(
                interaction.message.embeds[0].to_dict()
            )

            description = (
                embed.description or ""
            )

            description = re.sub(
                r"👨‍💼 \*\*Bearbeiter:\*\*.*",
                (
                    "👨‍💼 **Bearbeiter:** "
                    f"{interaction.user.mention}"
                ),
                description,
            )

            embed.description = description

            await interaction.response.edit_message(
                embed=embed,
                view=self,
            )

        else:

            await interaction.response.send_message(
                "✅ Ticket übernommen.",
                ephemeral=True,
            )

        await send_ticket_log(
            interaction.guild,
            "👤 Ticket übernommen",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Bearbeiter:** {interaction.user.mention}"
            ),
        )

    # --------------------------------------------------------
    # ADD USER
    # --------------------------------------------------------

    @discord.ui.button(
        label="Person hinzufügen",
        emoji="➕",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp_ticket_add_user",
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

        data, config = get_ticket_config(
            channel
        )

        if not data or not config:
            return

        role = interaction.guild.get_role(
            config["role_id"]
        )

        if not is_ticket_staff(
            interaction.user,
            role,
        ):

            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann Personen hinzufügen.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            AddUserModal()
        )

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    @discord.ui.button(
        label="Schließen",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp_ticket_close",
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

        data, config = get_ticket_config(
            channel
        )

        if not data or not config:
            return

        role = interaction.guild.get_role(
            config["role_id"]
        )

        if (
            interaction.user.id != data["owner_id"]
            and not is_ticket_staff(
                interaction.user,
                role,
            )
        ):

            await interaction.response.send_message(
                "❌ Du darfst dieses Ticket nicht schließen.",
                ephemeral=True,
            )

            return

        await interaction.response.defer()

        owner = interaction.guild.get_member(
            data["owner_id"]
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

        try:

            await channel.edit(
                name=(
                    f"closed-{channel.name}"
                )[:100]
            )

        except discord.HTTPException:
            pass

        await send_ticket_log(
            interaction.guild,
            "🔒 Ticket geschlossen",
            (
                f"**Ticket:** #{channel.name}\n"
                f"**Ersteller:** <@{data['owner_id']}>\n"
                f"**Geschlossen von:** {interaction.user.mention}\n"
                f"**Bereich:** {config['emoji']} {config['name']}"
            ),
            color=0xE67E22,
            file=transcript,
        )

        embed = discord.Embed(
            title="🔒 EHRP | TICKET GESCHLOSSEN",
            description=(
                "🔴 **Status:** Geschlossen\n\n"
                f"Geschlossen von {interaction.user.mention}\n\n"
                "Das zuständige Team kann das Ticket "
                "wieder öffnen oder endgültig löschen."
            ),
            color=0xE67E22,
        )

        embed.set_footer(
            text="EHRP | System • Ticket Control"
        )

        await interaction.message.edit(
            embed=embed,
            view=ClosedTicketView(),
        )


# ============================================================
# CLOSED VIEW
# ============================================================

class ClosedTicketView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    # --------------------------------------------------------
    # REOPEN
    # --------------------------------------------------------

    @discord.ui.button(
        label="Wieder öffnen",
        emoji="🔓",
        style=discord.ButtonStyle.success,
        custom_id="ehrp_ticket_reopen",
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

        data, config = get_ticket_config(
            channel
        )

        if not data or not config:
            return

        role = interaction.guild.get_role(
            config["role_id"]
        )

        if not is_ticket_staff(
            interaction.user,
            role,
        ):

            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann das Ticket wieder öffnen.",
                ephemeral=True,
            )

            return

        owner = interaction.guild.get_member(
            data["owner_id"]
        )

        if owner:

            try:

                await channel.set_permissions(
                    owner,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                )

            except discord.HTTPException:
                pass

        new_name = channel.name

        if new_name.startswith(
            "closed-"
        ):

            new_name = new_name[
                len("closed-"):
            ]

        try:

            await channel.edit(
                name=new_name
            )

        except discord.HTTPException:
            pass

        embed = discord.Embed(
            title="🔓 EHRP | TICKET WIEDER GEÖFFNET",
            description=(
                "🟢 **Status:** Offen\n\n"
                f"Wieder geöffnet von "
                f"{interaction.user.mention}."
            ),
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text="EHRP | System • Ticket Control"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=OpenTicketView(),
        )

        await send_ticket_log(
            interaction.guild,
            "🔓 Ticket wieder geöffnet",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Von:** {interaction.user.mention}"
            ),
        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    @discord.ui.button(
        label="Löschen",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp_ticket_delete",
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

        data, config = get_ticket_config(
            channel
        )

        if not data or not config:
            return

        role = interaction.guild.get_role(
            config["role_id"]
        )

        if not is_ticket_staff(
            interaction.user,
            role,
        ):

            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann Tickets löschen.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            (
                "⚠️ **Ticket endgültig löschen?**\n"
                "Dieser Vorgang kann nicht rückgängig gemacht werden."
            ),
            view=DeleteConfirmView(),
            ephemeral=True,
        )


# ============================================================
# DELETE CONFIRM
# ============================================================

class DeleteConfirmView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=60
        )

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
                f"**Ticket:** #{channel.name}\n"
                f"**Gelöscht von:** {interaction.user.mention}"
            ),
            color=0xE74C3C,
        )

        try:

            await channel.delete(
                reason=(
                    f"Ticket gelöscht von "
                    f"{interaction.user}"
                )
            )

        except discord.HTTPException:
            pass


# ============================================================
# ADD USER MODAL
# ============================================================

class AddUserModal(
    discord.ui.Modal,
    title="Person hinzufügen",
):

    user_id = discord.ui.TextInput(
        label="Discord User-ID",
        placeholder="123456789012345678",
        min_length=17,
        max_length=20,
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

        try:

            target_id = int(
                self.user_id.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Ungültige User-ID.",
                ephemeral=True,
            )

            return

        member = interaction.guild.get_member(
            target_id
        )

        if member is None:

            try:

                member = await interaction.guild.fetch_member(
                    target_id
                )

            except discord.HTTPException:
                member = None

        if member is None:

            await interaction.response.send_message(
                "❌ Mitglied nicht gefunden.",
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
            )

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ Mitglied konnte nicht hinzugefügt werden.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            (
                f"✅ {member.mention} wurde "
                "zum Ticket hinzugefügt."
            ),
            ephemeral=True,
        )

        await send_ticket_log(
            interaction.guild,
            "➕ Person hinzugefügt",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Person:** {member.mention}\n"
                f"**Hinzugefügt von:** {interaction.user.mention}"
            ),
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

        # Persistent UI
        self.bot.add_view(
            TicketPanelView()
        )

        self.bot.add_view(
            OpenTicketView()
        )

        self.bot.add_view(
            ClosedTicketView()
        )

    # --------------------------------------------------------
    # PANEL COMMAND
    # --------------------------------------------------------

    @app_commands.command(
        name="ticket_panel",
        description="Erstellt das EHRP Service Center.",
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        guild = interaction.guild

        channel = guild.get_channel(
            PANEL_CHANNEL_ID
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                "❌ Panel-Channel nicht gefunden.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            await channel.send(
                embed=build_main_panel(),
                view=TicketPanelView(),
            )

        except discord.HTTPException as error:

            await interaction.followup.send(
                (
                    "❌ Panel konnte nicht "
                    f"erstellt werden.\n`{error}`"
                ),
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            (
                "✅ **EHRP Service Center erstellt**\n\n"
                f"{channel.mention}"
            ),
            ephemeral=True,
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    @app_commands.command(
        name="ticket_status",
        description="Zeigt den Status des Ticket-Systems.",
    )
    async def ticket_status(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        tickets = 0

        for config in TICKET_TYPES.values():

            category = interaction.guild.get_channel(
                config["category_id"]
            )

            if not isinstance(
                category,
                discord.CategoryChannel,
            ):
                continue

            for channel in category.text_channels:

                if read_topic(channel):
                    tickets += 1

        await interaction.response.send_message(
            (
                "## ⚙️ EHRP | TICKET SYSTEM\n\n"
                f"📂 Ticketbereiche: **{len(TICKET_TYPES)}**\n"
                f"🎫 Aktuelle Tickets: **{tickets}**\n\n"
                "🟢 Panel: ONLINE\n"
                "🟢 Routing: ONLINE\n"
                "🟢 Logging: ONLINE\n"
                "🟢 Persistent Controls: ONLINE"
            ),
            ephemeral=True,
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        Tickets(bot)
    )
