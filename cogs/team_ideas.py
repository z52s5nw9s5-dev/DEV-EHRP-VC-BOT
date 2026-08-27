from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# EHRP | SYSTEM — TEAM IDEEN
# ============================================================

PANEL_CHANNEL_ID = 1534888848004481116
IDEAS_CHANNEL_ID = 1526937967162298418

TEAM_PING_ROLE_ID = 1526956922555732151

FOUNDER_ROLE_ID = 1526952807838646334
CO_FOUNDER_ROLE_ID = 1526952825169510473

GERMAN_TZ = ZoneInfo("Europe/Berlin")

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245


# ============================================================
# TEAM ROLLEN
# ============================================================

TEAM_ROLE_IDS = {
    1526952807838646334,
    1526952825169510473,
    1526952877585596570,
    1526952894891556864,
    1536099715412926584,
    1526952911651995649,
    1526953865768075435,
    1536100042354462802,
    1532505961292501084,
    1526955267416133653,
    1526955292514980003,
    1532506490852737104,
    1532506146898706604,
    1526953952199839935,
    1526953970294063194,
    1532520713657909278,
    1526956576701677589,
    1526956609048416429,
    1526956627704549408,
    1526956664253579294,
    1526956700836429944,
    1526956724089524386,
    1532504668859662376,
    1532504388503994568,
    1526956760303140924,
    1526956795590086747,
    1526956832822919331,
}


# ============================================================
# BERECHTIGUNGEN
# ============================================================

def is_team_member(member: discord.Member) -> bool:
    return any(
        role.id in TEAM_ROLE_IDS
        for role in member.roles
    )


def can_review(member: discord.Member) -> bool:
    allowed = {
        FOUNDER_ROLE_ID,
        CO_FOUNDER_ROLE_ID,
    }

    return any(
        role.id in allowed
        for role in member.roles
    )


def get_highest_team_role(member: discord.Member) -> str:
    team_roles = [
        role
        for role in member.roles
        if role.id in TEAM_ROLE_IDS
    ]

    if not team_roles:
        return "Teammitglied"

    highest = max(
        team_roles,
        key=lambda role: role.position,
    )

    return highest.name.replace("»", "").strip()


# ============================================================
# PANEL
# ============================================================

def build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="💡 EHRP | TEAM IDEEN",
        description=(
            "## DEINE IDEE ZÄHLT\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Du hast eine Idee für den Server, das Team "
            "oder das Roleplay?\n\n"
            "Dann kannst du sie hier direkt einreichen.\n\n"
            "💡 **So funktioniert es:**\n"
            "• Klicke auf **Idee einreichen**\n"
            "• Fülle das Formular aus\n"
            "• Deine Idee wird automatisch gepostet\n"
            "• Das Team wird informiert\n"
            "• Founder oder Co-Founder prüfen die Idee\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_footer(
        text="EHRP | System • Team Ideen"
    )

    return embed


# ============================================================
# IDEEN EMBED
# ============================================================

def build_idea_embed(
    member: discord.Member,
    title: str,
    description: str,
    benefit: str,
) -> discord.Embed:

    now = datetime.now(GERMAN_TZ)

    embed = discord.Embed(
        title=f"💡 TEAM IDEE | {title}",
        description="━━━━━━━━━━━━━━━━━━━━",
        color=SYSTEM_COLOR,
        timestamp=now,
    )

    embed.add_field(
        name="👤 Eingereicht von",
        value=member.mention,
        inline=True,
    )

    embed.add_field(
        name="🏷️ Rang",
        value=get_highest_team_role(member),
        inline=True,
    )

    embed.add_field(
        name="📅 Eingereicht",
        value=now.strftime("%d.%m.%Y • %H:%M Uhr"),
        inline=False,
    )

    embed.add_field(
        name="💭 Idee",
        value=description[:1024],
        inline=False,
    )

    embed.add_field(
        name="✅ Nutzen / Verbesserung",
        value=benefit[:1024],
        inline=False,
    )

    embed.add_field(
        name="📌 Status",
        value="⚪ **Offen**",
        inline=False,
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=f"EHRP | System • User-ID: {member.id}"
    )

    return embed


# ============================================================
# STATUS ÄNDERN
# ============================================================

async def update_idea_status(
    interaction: discord.Interaction,
    status_text: str,
    color: int,
):
    if not isinstance(interaction.user, discord.Member):
        return

    if not can_review(interaction.user):
        await interaction.response.send_message(
            "❌ Nur Founder oder Co-Founder dürfen Ideen bearbeiten.",
            ephemeral=True,
        )
        return

    if not interaction.message or not interaction.message.embeds:
        await interaction.response.send_message(
            "❌ Idee konnte nicht geladen werden.",
            ephemeral=True,
        )
        return

    embed = interaction.message.embeds[0]

    new_embed = discord.Embed.from_dict(
        embed.to_dict()
    )

    new_embed.color = color

    found = False

    for index, field in enumerate(new_embed.fields):
        if field.name == "📌 Status":
            new_embed.set_field_at(
                index,
                name="📌 Status",
                value=status_text,
                inline=False,
            )
            found = True
            break

    if not found:
        new_embed.add_field(
            name="📌 Status",
            value=status_text,
            inline=False,
        )

    new_embed.add_field(
        name="👑 Bearbeitet von",
        value=interaction.user.mention,
        inline=False,
    )

    await interaction.response.edit_message(
        embed=new_embed,
        view=IdeaReviewView(),
    )


# ============================================================
# REVIEW BUTTONS
# ============================================================

class IdeaReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Annehmen",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:teamidea:accept",
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await update_idea_status(
            interaction,
            "✅ **Angenommen**",
            SUCCESS_COLOR,
        )

    @discord.ui.button(
        label="In Prüfung",
        emoji="🟡",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:teamidea:review",
    )
    async def review(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await update_idea_status(
            interaction,
            "🟡 **In Prüfung**",
            WARNING_COLOR,
        )

    @discord.ui.button(
        label="Ablehnen",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:teamidea:reject",
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await update_idea_status(
            interaction,
            "❌ **Abgelehnt**",
            ERROR_COLOR,
        )


# ============================================================
# MODAL
# ============================================================

class TeamIdeaModal(
    discord.ui.Modal,
    title="💡 Team-Idee einreichen",
):

    idea_title = discord.ui.TextInput(
        label="Titel der Idee",
        placeholder="Kurzer Titel...",
        max_length=100,
        required=True,
    )

    idea_description = discord.ui.TextInput(
        label="Beschreibe deine Idee",
        placeholder="Was möchtest du ändern oder hinzufügen?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    idea_benefit = discord.ui.TextInput(
        label="Warum ist das sinnvoll?",
        placeholder="Was würde sich dadurch verbessern?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        if (
            interaction.guild is None
            or not isinstance(
                interaction.user,
                discord.Member,
            )
        ):
            await interaction.response.send_message(
                "❌ Dieser Bereich funktioniert nur auf dem Server.",
                ephemeral=True,
            )
            return

        if not is_team_member(
            interaction.user
        ):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder dürfen Ideen einreichen.",
                ephemeral=True,
            )
            return

        ideas_channel = interaction.guild.get_channel(
            IDEAS_CHANNEL_ID
        )

        if not isinstance(
            ideas_channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Ideen-Channel wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        team_role = interaction.guild.get_role(
            TEAM_PING_ROLE_ID
        )

        embed = build_idea_embed(
            interaction.user,
            str(self.idea_title),
            str(self.idea_description),
            str(self.idea_benefit),
        )

        ping_text = (
            team_role.mention
            if team_role
            else "Team"
        )

        await ideas_channel.send(
            content=f"💡 Neue Team-Idee • {ping_text}",
            embed=embed,
            view=IdeaReviewView(),
            allowed_mentions=discord.AllowedMentions(
                roles=True,
                users=False,
                everyone=False,
            ),
        )

        await interaction.response.send_message(
            "✅ Deine Team-Idee wurde erfolgreich eingereicht.",
            ephemeral=True,
        )


# ============================================================
# PANEL BUTTON
# ============================================================

class TeamIdeaPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Idee einreichen",
        emoji="💡",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:teamidea:submit",
    )
    async def submit_idea(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return

        if not is_team_member(
            interaction.user
        ):
            await interaction.response.send_message(
                "❌ Nur Teammitglieder dürfen Ideen einreichen.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            TeamIdeaModal()
        )


# ============================================================
# COG
# ============================================================

class TeamIdeas(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        bot.add_view(
            TeamIdeaPanelView()
        )

        bot.add_view(
            IdeaReviewView()
        )

    async def find_panel(
        self,
        channel: discord.TextChannel,
    ):
        try:
            async for message in channel.history(
                limit=30
            ):
                if (
                    self.bot.user
                    and message.author.id == self.bot.user.id
                    and message.embeds
                    and message.embeds[0].title
                    == "💡 EHRP | TEAM IDEEN"
                ):
                    return message

        except discord.HTTPException:
            pass

        return None

    @app_commands.command(
        name="teamideen_panel",
        description="Erstellt das dauerhafte Team-Ideen Panel.",
    )
    async def teamideen_panel(
        self,
        interaction: discord.Interaction,
    ):

        if (
            interaction.guild is None
            or not isinstance(
                interaction.user,
                discord.Member,
            )
        ):
            return

        if not can_review(
            interaction.user
        ):
            await interaction.response.send_message(
                "❌ Nur Founder oder Co-Founder dürfen das Panel erstellen.",
                ephemeral=True,
            )
            return

        panel_channel = interaction.guild.get_channel(
            PANEL_CHANNEL_ID
        )

        if not isinstance(
            panel_channel,
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

        existing = await self.find_panel(
            panel_channel
        )

        if existing:
            await existing.edit(
                embed=build_panel_embed(),
                view=TeamIdeaPanelView(),
            )

            await interaction.followup.send(
                "✅ Team-Ideen Panel wurde aktualisiert.",
                ephemeral=True,
            )
            return

        await panel_channel.send(
            embed=build_panel_embed(),
            view=TeamIdeaPanelView(),
        )

        await interaction.followup.send(
            f"✅ Team-Ideen Panel wurde in {panel_channel.mention} erstellt.",
            ephemeral=True,
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        TeamIdeas(bot)
    )
