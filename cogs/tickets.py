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
        "description": "Stelle einen Antrag auf Entbannung.",
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
        "description": "Social Media, Content und Medienanfragen.",
        "category_id": 1526938931013222570,
        "role_id": 1526956524466081802,
    },

    "developer": {
        "name": "Developer",
        "emoji": "💻",
        "description": "Technische Probleme, Bugs und Development.",
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


SYSTEM_COLOR = 0x3388FF


# ============================================================
# HELPERS
# ============================================================

def clean_channel_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9äöüß\-]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")[:40]


def make_ticket_topic(
    ticket_type: str,
    owner_id: int,
    claimed_id: int | None = None,
):
    claimed = claimed_id if claimed_id else 0

    return (
        f"EHRP_TICKET|"
        f"type={ticket_type}|"
        f"owner={owner_id}|"
        f"claimed={claimed}"
    )


def read_ticket_topic(channel: discord.TextChannel):
    topic = channel.topic or ""

    if not topic.startswith("EHRP_TICKET|"):
        return None

    result = {}

    for part in topic.split("|")[1:]:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        result[key] = value

    try:
        return {
            "type": result["type"],
            "owner_id": int(result["owner"]),
            "claimed_id": int(result.get("claimed", "0")),
        }
    except (KeyError, ValueError):
        return None


def ticket_config_from_channel(channel: discord.TextChannel):
    data = read_ticket_topic(channel)

    if not data:
        return None, None

    return data, TICKET_TYPES.get(data["type"])


async def ticket_log(
    guild: discord.Guild,
    title: str,
    description: str,
    color: int = SYSTEM_COLOR,
    file: discord.File | None = None,
):
    channel = guild.get_channel(TICKET_LOG_CHANNEL_ID)

    if not isinstance(channel, discord.TextChannel):
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
        if file:
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)

    except discord.HTTPException:
        pass


async def make_transcript(channel: discord.TextChannel):
    lines = [
        "EHRP | SYSTEM — TICKET TRANSCRIPT",
        f"Channel: #{channel.name}",
        f"Channel-ID: {channel.id}",
        "",
        "============================================",
        "",
    ]

    try:
        async for message in channel.history(
            limit=1000,
            oldest_first=True,
        ):
            created = message.created_at.strftime(
                "%d.%m.%Y %H:%M:%S"
            )

            content = message.content or ""

            if message.attachments:
                urls = " ".join(
                    attachment.url
                    for attachment in message.attachments
                )

                if content:
                    content += f" | Anhänge: {urls}"
                else:
                    content = f"Anhänge: {urls}"

            if not content and message.embeds:
                content = "[Embed / System-Nachricht]"

            lines.append(
                f"[{created}] "
                f"{message.author} ({message.author.id}): "
                f"{content}"
            )

    except discord.HTTPException:
        return None

    data = "\n".join(lines).encode("utf-8")

    return discord.File(
        io.BytesIO(data),
        filename=f"{channel.name}-transcript.txt",
    )


async def user_has_open_ticket(
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
        data = read_ticket_topic(channel)

        if not data:
            continue

        if (
            data["owner_id"] == user_id
            and data["type"] == ticket_type
        ):
            return channel

    return None


# ============================================================
# TICKET PANEL
# ============================================================

def build_main_panel():
    embed = discord.Embed(
        title="EHRP | SERVICE CENTER",
        description=(
            "### Willkommen im zentralen Service Center\n"
            "Hier kannst du dein Anliegen direkt an die "
            "zuständige Abteilung weiterleiten.\n\n"
            "```ansi\n"
            "\u001b[2;32m● SYSTEM ONLINE\u001b[0m\n"
            "\u001b[2;34m● TICKET ROUTING ACTIVE\u001b[0m\n"
            "\u001b[2;36m● PRIVATE SESSION ENABLED\u001b[0m\n"
            "```\n"
            "### Neues Anliegen\n"
            "Wähle unten den passenden Bereich aus.\n\n"
            "🔒 **Privat** — nur du und das zuständige Team\n"
            "⚡ **Automatisch** — Weiterleitung an die richtige Abteilung\n"
            "🛡️ **Geschützt** — internes Ticket-Logging"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_author(
        name="EHRP | SYSTEM",
    )

    embed.set_footer(
        text="EHRP | System • Service Portal"
    )

    return embed


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
            placeholder="Bereich auswählen …",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ehrp:ticket:type_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        ticket_type = self.values[0]

        await interaction.response.send_modal(
            TicketCreateModal(ticket_type)
        )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(TicketSelect())


# ============================================================
# CREATE MODAL
# ============================================================

class TicketCreateModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        self.ticket_type = ticket_type

        config = TICKET_TYPES[ticket_type]

        super().__init__(
            title=f"{config['emoji']} {config['name']} • Neues Ticket"
        )

        if ticket_type == "entbannung":
            self.field_one = discord.ui.TextInput(
                label="Ingame-Name",
                placeholder="Wie lautet dein Name im RP?",
                max_length=100,
            )

            self.field_two = discord.ui.TextInput(
                label="Banngrund",
                placeholder="Warum wurdest du gebannt?",
                style=discord.TextStyle.paragraph,
                max_length=500,
            )

            self.field_three = discord.ui.TextInput(
                label="Begründung für die Entbannung",
                placeholder="Warum möchtest du entbannt werden?",
                style=discord.TextStyle.paragraph,
                max_length=1000,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)
            self.add_item(self.field_three)

        elif ticket_type == "developer":
            self.field_one = discord.ui.TextInput(
                label="System / Fehler",
                placeholder="Was funktioniert nicht?",
                max_length=150,
            )

            self.field_two = discord.ui.TextInput(
                label="Beschreibung",
                placeholder=(
                    "Beschreibe den Fehler möglichst genau. "
                    "Was hast du gemacht und was ist passiert?"
                ),
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)

        elif ticket_type == "immobilien":
            self.field_one = discord.ui.TextInput(
                label="Immobilie / Ort",
                placeholder="Um welche Immobilie geht es?",
                max_length=150,
            )

            self.field_two = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)

        elif ticket_type == "fraktion":
            self.field_one = discord.ui.TextInput(
                label="Fraktion",
                placeholder="Welche Fraktion betrifft dein Anliegen?",
                max_length=150,
            )

            self.field_two = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)

        elif ticket_type == "socialmedia":
            self.field_one = discord.ui.TextInput(
                label="Plattform / Thema",
                placeholder="TikTok, YouTube, Instagram, Kooperation …",
                max_length=150,
            )

            self.field_two = discord.ui.TextInput(
                label="Anliegen",
                placeholder="Beschreibe dein Anliegen.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)

        else:
            self.field_one = discord.ui.TextInput(
                label="Betreff",
                placeholder="Worum geht es?",
                max_length=150,
            )

            self.field_two = discord.ui.TextInput(
                label="Beschreibung",
                placeholder="Beschreibe dein Anliegen möglichst genau.",
                style=discord.TextStyle.paragraph,
                max_length=1500,
            )

            self.add_item(self.field_one)
            self.add_item(self.field_two)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        guild = interaction.guild

        if guild is None:
            return

        config = TICKET_TYPES[self.ticket_type]

        existing = await user_has_open_ticket(
            guild,
            interaction.user.id,
            self.ticket_type,
        )

        if existing:
            await interaction.response.send_message(
                (
                    "⚠️ Du hast in diesem Bereich bereits "
                    f"ein offenes Ticket: {existing.mention}"
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
                "❌ Die Ticket-Kategorie wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        if support_role is None:
            await interaction.response.send_message(
                "❌ Die zuständige Teamrolle wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        bot_member = guild.me

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),

            support_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
        }

        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True,
            )

        base_name = clean_channel_name(
            interaction.user.display_name
        )

        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{base_name}",
                category=category,
                overwrites=overwrites,
                topic=make_ticket_topic(
                    self.ticket_type,
                    interaction.user.id,
                ),
                reason=(
                    f"EHRP Ticket erstellt durch "
                    f"{interaction.user}"
                ),
            )

        except discord.HTTPException:
            await interaction.followup.send(
                "❌ Das Ticket konnte nicht erstellt werden.",
                ephemeral=True,
            )
            return

        ticket_number = str(channel.id)[-6:]

        try:
            await channel.edit(
                name=f"{config['emoji']}-ticket-{ticket_number}"
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
                "### Ticket erfolgreich erstellt\n"
                "Dein Anliegen wurde an die zuständige "
                "Abteilung weitergeleitet.\n\n"
                "**Status:** 🟢 Offen\n"
                f"**Bereich:** {config['emoji']} {config['name']}\n"
                f"**Ersteller:** {interaction.user.mention}\n"
                f"**Zuständig:** {support_role.mention}\n"
                "**Bearbeiter:** Nicht übernommen"
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

        ticket_message = await channel.send(
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

        await ticket_log(
            guild,
            "🎫 Ticket erstellt",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**ID:** `{ticket_number}`\n"
                f"**Typ:** {config['emoji']} {config['name']}\n"
                f"**Ersteller:** {interaction.user.mention}\n"
                f"**Team:** {support_role.mention}"
            ),
        )

        await interaction.followup.send(
            (
                "✅ **Ticket erstellt**\n\n"
                f"Dein Ticket: {channel.mention}"
            ),
            ephemeral=True,
        )


# ============================================================
# OPEN TICKET CONTROLS
# ============================================================

class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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

        data, config = ticket_config_from_channel(
            channel
        )

        if not data or not config:
            await interaction.response.send_message(
                "❌ Ungültiges Ticket.",
                ephemeral=True,
            )
            return

        support_role = interaction.guild.get_role(
            config["role_id"]
        )

        if (
            support_role not in interaction.user.roles
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "❌ Du bist für diesen Ticketbereich nicht zuständig.",
                ephemeral=True,
            )
            return

        if data["claimed_id"]:
            member = interaction.guild.get_member(
                data["claimed_id"]
            )

            await interaction.response.send_message(
                (
                    "⚠️ Dieses Ticket wurde bereits von "
                    f"{member.mention if member else 'einem Teammitglied'} "
                    "übernommen."
                ),
                ephemeral=True,
            )
            return

        await channel.edit(
            topic=make_ticket_topic(
                data["type"],
                data["owner_id"],
                interaction.user.id,
            ),
            reason="EHRP Ticket übernommen",
        )

        embed = interaction.message.embeds[0]

        new_embed = discord.Embed.from_dict(
            embed.to_dict()
        )

        description = new_embed.description or ""

        description = re.sub(
            r"\*\*Bearbeiter:\*\*.*",
            f"**Bearbeiter:** {interaction.user.mention}",
            description,
        )

        new_embed.description = description

        await interaction.response.edit_message(
            embed=new_embed,
            view=self,
        )

        await ticket_log(
            interaction.guild,
            "👤 Ticket übernommen",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Bearbeiter:** {interaction.user.mention}"
            ),
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
        await interaction.response.send_modal(
            AddUserModal()
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

        data, config = ticket_config_from_channel(
            channel
        )

        if not data or not config:
            return

        await interaction.response.defer()

        owner = interaction.guild.get_member(
            data["owner_id"]
        )

        if owner:
            try:
                await channel.set_permissions(
                    owner,
                    send_messages=False,
                    view_channel=True,
                    read_message_history=True,
                )
            except discord.HTTPException:
                pass

        if not channel.name.startswith("closed-"):
            try:
                await channel.edit(
                    name=f"closed-{channel.name}"[:100],
                    reason="EHRP Ticket geschlossen",
                )
            except discord.HTTPException:
                pass

        transcript = await make_transcript(
            channel
        )

        await ticket_log(
            interaction.guild,
            "🔒 Ticket geschlossen",
            (
                f"**Ticket:** #{channel.name}\n"
                f"**Ersteller:** "
                f"<@{data['owner_id']}>\n"
                f"**Geschlossen von:** "
                f"{interaction.user.mention}\n"
                f"**Typ:** {config['emoji']} {config['name']}"
            ),
            color=0xE67E22,
            file=transcript,
        )

        embed = discord.Embed(
            title="🔒 EHRP | TICKET GESCHLOSSEN",
            description=(
                "**Status:** 🔴 Geschlossen\n\n"
                f"Geschlossen von {interaction.user.mention}\n\n"
                "Das Ticket kann vom Team wieder geöffnet "
                "oder endgültig gelöscht werden."
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

        data, config = ticket_config_from_channel(
            channel
        )

        if not data or not config:
            return

        support_role = interaction.guild.get_role(
            config["role_id"]
        )

        if (
            support_role not in interaction.user.roles
            and not interaction.user.guild_permissions.administrator
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

        if new_name.startswith("closed-"):
            new_name = new_name[7:]

        try:
            await channel.edit(
                name=new_name,
                reason="EHRP Ticket wieder geöffnet",
            )
        except discord.HTTPException:
            pass

        embed = discord.Embed(
            title="🔓 EHRP | TICKET WIEDER GEÖFFNET",
            description=(
                "**Status:** 🟢 Offen\n\n"
                f"Wieder geöffnet von {interaction.user.mention}."
            ),
            color=SYSTEM_COLOR,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=OpenTicketView(),
        )

        await ticket_log(
            interaction.guild,
            "🔓 Ticket wieder geöffnet",
            (
                f"**Ticket:** {channel.mention}\n"
                f"**Von:** {interaction.user.mention}"
            ),
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

        data, config = ticket_config_from_channel(
            channel
        )

        if not data or not config:
            return

        support_role = interaction.guild.get_role(
            config["role_id"]
        )

        if (
            support_role not in interaction.user.roles
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "❌ Nur das zuständige Team kann dieses Ticket löschen.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "⚠️ Ticket wirklich endgültig löschen?",
            view=DeleteConfirmView(),
            ephemeral=True,
        )


class DeleteConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Ja, endgültig löschen",
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

        await ticket_log(
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
                    f"EHRP Ticket gelöscht von "
                    f"{interaction.user}"
                )
            )
        except discord.HTTPException:
            pass


# ============================================================
# ADD USER
# ============================================================

class AddUserModal(
    discord.ui.Modal,
    title="Person zum Ticket hinzufügen",
):
    user_id = discord.ui.TextInput(
        label="Discord User-ID",
        placeholder="z. B. 123456789012345678",
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
            user_id = int(self.user_id.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ Ungültige User-ID.",
                ephemeral=True,
            )
            return

        member = interaction.guild.get_member(
            user_id
        )

        if member is None:
            try:
                member = await interaction.guild.fetch_member(
                    user_id
                )
            except discord.HTTPException:
                member = None

        if member is None:
            await interaction.response.send_message(
                "❌ User wurde nicht gefunden.",
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
                "❌ User konnte nicht hinzugefügt werden.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ {member.mention} wurde zum Ticket hinzugefügt.",
            ephemeral=True,
        )

        await ticket_log(
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
    def __init__(self, bot):
        self.bot = bot

        # Persistent Views
        bot.add_view(TicketPanelView())
        bot.add_view(OpenTicketView())
        bot.add_view(ClosedTicketView())

    @app_commands.command(
        name="ticket_panel",
        description="Erstellt oder erneuert das EHRP Service Center.",
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        channel = interaction.guild.get_channel(
            PANEL_CHANNEL_ID
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Panel-Channel wurde nicht gefunden.",
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
                f"❌ Fehler beim Erstellen des Panels:\n`{error}`",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            (
                "✅ **EHRP Service Center erstellt**\n\n"
                f"Panel: {channel.mention}"
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="ticket_status",
        description="Zeigt den Status des EHRP Ticket-Systems.",
    )
    async def ticket_status(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        open_tickets = 0

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
                if read_ticket_topic(channel):
                    open_tickets += 1

        await interaction.response.send_message(
            (
                "⚙️ **EHRP | SYSTEM • TICKET STATUS**\n\n"
                f"🎫 Ticketbereiche: **{len(TICKET_TYPES)}**\n"
                f"📂 Aktuelle Tickets: **{open_tickets}**\n"
                "🟢 Routing: **ONLINE**\n"
                "🟢 Logging: **ONLINE**\n"
                "🟢 Persistent Controls: **ONLINE**"
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Tickets(bot))
