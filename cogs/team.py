from __future__ import annotations

import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — TEAM CONFIG
# ============================================================

TEAM_STRUCTURE = [
    (
        "👑 Leitung",
        [
            ("Founder", "[FD]"),
            ("Co-Founder", "[Co. FD]"),
        ],
    ),
    (
        "⚜️ Leaderebene",
        [
            ("Obervorstand", "[OVS]"),
            ("Vorstand", "[VS]"),
            ("Sachbearbeiter", "[SB]"),
            ("Verwaltungsleitung", "[VL]"),
            ("Hauptverwaltung", "[HV]"),
        ],
    ),
    (
        "💎 Kernteam",
        [
            ("Archivleitung", "[AL]"),
            ("Gesamtkoordinator", "[GT. K]"),
            ("Teamkoordinator", "[T. K]"),
            ("Jr. Teamkoordinator", "[Jr. T. K]"),
        ],
    ),
    (
        "🛡️ Teamverwaltung",
        [
            ("Head of Management", "[HoM]"),
            ("Sr. Management", "[Sr. M]"),
            ("Manager", "[M]"),
            ("Stv. Manager", "[Stv. M]"),
        ],
    ),
    (
        "⚙️ Management",
        [
            ("Admin-Koordinator", "[A. K]"),
            ("Systemadministrator", "[SYS. A]"),
            ("Administrator", "[ADM]"),
            ("Jr. Administrator", "[Jr. ADM]"),
        ],
    ),
    (
        "🔨 Administration",
        [
            ("Mod-Koordinator", "[MOD. K]"),
            ("Moderations-Spezialist", "[MOD. S]"),
            ("Moderator", "[MOD]"),
            ("Jr. Moderator", "[Jr. MOD]"),
        ],
    ),
    (
        "🎧 Moderation & Support",
        [
            ("Sup-Koordinator", "[SUP. K]"),
            ("Support-Spezialist", "[SUP. S]"),
            ("Supporter", "[SUP]"),
            ("Az. Supporter", "[Az. SUP]"),
        ],
    ),
]


ABSENCE_KEYWORDS = (
    "abgemeldet",
    "abwesen",
    "absence",
)

TEAM_EMBED_TITLE = "👥 EHRP | SYSTEM • TEAMLISTE"
TEAM_FOOTER_MARKER = "EHRP_TEAMLIST_V2"

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C


# ============================================================
# ACCESS
# ============================================================

async def ensure_dev(
    interaction: discord.Interaction,
) -> bool:

    if (
        not interaction.guild
        or not isinstance(
            interaction.user,
            discord.Member,
        )
    ):
        await interaction.response.send_message(
            "❌ Dieser Befehl funktioniert nur auf dem Server.",
            ephemeral=True,
        )
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    try:
        dev_role_id = int(
            DEV_ROLE_ID
        )
    except (TypeError, ValueError):
        dev_role_id = 0

    dev_role = interaction.guild.get_role(
        dev_role_id
    )

    if (
        dev_role
        and dev_role in interaction.user.roles
    ):
        return True

    await interaction.response.send_message(
        "❌ Du darfst diese Systemfunktion nicht benutzen.",
        ephemeral=True,
    )

    return False


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(
    value: str,
) -> str:

    value = value.lower().strip()

    value = (
        value
        .replace("»", "")
        .replace("➡", "")
        .replace("↪", "")
        .replace("→", "")
        .replace("•", "")
        .replace("|", "")
        .replace("—", "")
    )

    value = re.sub(
        r"[^a-z0-9äöüß]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def find_role(
    guild: discord.Guild,
    wanted_name: str,
) -> discord.Role | None:

    wanted = normalize(
        wanted_name
    )

    for role in guild.roles:

        if normalize(role.name) == wanted:
            return role

    return None


# ============================================================
# ABSENCE
# ============================================================

def member_is_absent(
    member: discord.Member,
) -> bool:

    for role in member.roles:

        role_name = normalize(
            role.name
        )

        if any(
            keyword in role_name
            for keyword in ABSENCE_KEYWORDS
        ):
            return True

    return False


# ============================================================
# TEAM ROLE DETECTION
# ============================================================

def get_team_role_data(
    member: discord.Member,
):
    """
    Gibt den höchsten Teamrang zurück.

    Rückgabe:
    {
        "section": "...",
        "role_name": "...",
        "role": discord.Role,
        "prefix": "[...]"
    }

    oder None.
    """

    for section_name, roles in TEAM_STRUCTURE:

        for role_name, prefix in roles:

            wanted = normalize(
                role_name
            )

            for member_role in member.roles:

                if normalize(
                    member_role.name
                ) == wanted:

                    return {
                        "section": section_name,
                        "role_name": role_name,
                        "role": member_role,
                        "prefix": prefix,
                    }

    return None


def is_team_member(
    member: discord.Member,
) -> bool:

    return (
        get_team_role_data(member)
        is not None
    )


# ============================================================
# NICKNAMES
# ============================================================

def clean_member_name(
    member: discord.Member,
) -> str:

    name = (
        member.nick
        or member.global_name
        or member.name
    )

    # Abgemeldet entfernen
    name = re.sub(
        r"\s*-\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # Alte bekannte Präfixe entfernen
    for _, roles in TEAM_STRUCTURE:

        for _, prefix in roles:

            if name.startswith(
                prefix
            ):
                name = name[
                    len(prefix):
                ].strip()

    # Falls vorher ähnliche [...] Kürzel gesetzt wurden
    name = re.sub(
        r"^\[[^\]]{1,20}\]\s*",
        "",
        name,
    )

    return (
        name.strip()
        or member.name
    )


def desired_nickname(
    member: discord.Member,
) -> str | None:

    team_data = get_team_role_data(
        member
    )

    if not team_data:
        return None

    base_name = clean_member_name(
        member
    )

    nickname = (
        f"{team_data['prefix']} "
        f"{base_name}"
    )

    if member_is_absent(member):
        nickname += " - Abgemeldet"

    return nickname[:32]


async def update_member_nickname(
    member: discord.Member,
) -> bool:

    if member.bot:
        return False

    team_data = get_team_role_data(
        member
    )

    if not team_data:
        return False

    desired = desired_nickname(
        member
    )

    if not desired:
        return False

    if member.nick == desired:
        return False

    guild = member.guild

    bot_member = guild.me

    if bot_member is None:
        return False

    # Serverbesitzer kann Discord nicht umbenennen
    if member.id == guild.owner_id:
        return False

    # Bot muss über der Zielrolle stehen
    if (
        member.top_role
        >= bot_member.top_role
    ):
        print(
            "⚠️ Nickname nicht änderbar: "
            f"{member} | Rolle zu hoch"
        )
        return False

    try:
        await member.edit(
            nick=desired,
            reason=(
                "EHRP | System "
                "automatischer Team-Nickname"
            ),
        )

        return True

    except discord.Forbidden:

        print(
            "⚠️ Keine Berechtigung für Nickname: "
            f"{member}"
        )

    except discord.HTTPException as error:

        print(
            "❌ Nickname Fehler "
            f"{member}: {error}"
        )

    return False


# ============================================================
# TEAM MEMBERS
# ============================================================

def all_team_members(
    guild: discord.Guild,
) -> list[discord.Member]:

    members = []

    for member in guild.members:

        if (
            not member.bot
            and is_team_member(member)
        ):
            members.append(
                member
            )

    return members


def members_for_role(
    guild: discord.Guild,
    role_name: str,
) -> list[discord.Member]:

    role = find_role(
        guild,
        role_name,
    )

    if role is None:
        return []

    members = [
        member
        for member in role.members
        if not member.bot
    ]

    members.sort(
        key=lambda member:
        member.display_name.lower()
    )

    return members


# ============================================================
# TEAM EMBED
# ============================================================

def build_team_embed(
    guild: discord.Guild,
) -> discord.Embed:

    team_members = all_team_members(
        guild
    )

    absent_count = sum(
        1
        for member in team_members
        if member_is_absent(member)
    )

    active_count = (
        len(team_members)
        - absent_count
    )

    embed = discord.Embed(
        title=TEAM_EMBED_TITLE,
        description=(
            "## OFFIZIELLE TEAMÜBERSICHT\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** "
            f"{len(team_members)}\n"
            f"🟢 **Aktiv:** "
            f"{active_count}\n"
            f"🏖️ **Abgemeldet:** "
            f"{absent_count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Die Teamliste wird automatisch "
            "mit den Discord-Rollen synchronisiert."
        ),
        color=SYSTEM_COLOR,
    )

    for section_name, roles in TEAM_STRUCTURE:

        lines = []

        for role_name, prefix in roles:

            members = members_for_role(
                guild,
                role_name,
            )

            if members:

                member_text = " ".join(
                    member.mention
                    for member in members
                )

            else:

                member_text = "—"

            lines.append(
                f"**{prefix} {role_name}**\n"
                f"{member_text}"
            )

        embed.add_field(
            name=section_name,
            value="\n\n".join(
                lines
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{TEAM_FOOTER_MARKER} • "
            "Auto-Sync aktiv"
        )
    )

    return embed


# ============================================================
# FIND EXISTING TEAM MESSAGE
# ============================================================

async def find_team_message(
    guild: discord.Guild,
):

    bot_user = guild.me

    if bot_user is None:
        return None

    for channel in guild.text_channels:

        permissions = channel.permissions_for(
            bot_user
        )

        if not (
            permissions.view_channel
            and permissions.read_message_history
        ):
            continue

        try:

            async for message in channel.history(
                limit=50
            ):

                if (
                    message.author.id
                    != bot_user.id
                ):
                    continue

                if not message.embeds:
                    continue

                embed = message.embeds[0]

                footer = (
                    embed.footer.text
                    if embed.footer
                    else ""
                )

                if (
                    TEAM_FOOTER_MARKER
                    in footer
                ):
                    return message

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            continue

    return None


# ============================================================
# COG
# ============================================================

class Team(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        self.team_sync_loop.start()

    def cog_unload(
        self,
    ):
        self.team_sync_loop.cancel()

    # --------------------------------------------------------
    # FULL SYNC
    # --------------------------------------------------------

    async def full_sync(
        self,
        guild: discord.Guild,
    ):

        changed = 0

        for member in guild.members:

            if (
                member.bot
                or not is_team_member(member)
            ):
                continue

            if await update_member_nickname(
                member
            ):
                changed += 1

        message = await find_team_message(
            guild
        )

        if message:

            try:

                await message.edit(
                    embed=build_team_embed(
                        guild
                    )
                )

            except discord.HTTPException as error:

                print(
                    "❌ Teamliste Update Fehler: "
                    f"{error}"
                )

        return changed

    # --------------------------------------------------------
    # AUTO LOOP
    # --------------------------------------------------------

    @tasks.loop(
        minutes=5
    )
    async def team_sync_loop(
        self,
    ):

        for guild in self.bot.guilds:

            try:

                await self.full_sync(
                    guild
                )

            except Exception as error:

                print(
                    "❌ Team Auto-Sync Fehler "
                    f"{guild.name}: {error}"
                )

    @team_sync_loop.before_loop
    async def before_team_sync(
        self,
    ):

        await self.bot.wait_until_ready()

    # --------------------------------------------------------
    # ROLE / NICKNAME CHANGE
    # --------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):

        # Nur reagieren wenn Rollen oder Nickname
        # wirklich geändert wurden
        if (
            before.roles == after.roles
            and before.nick == after.nick
        ):
            return

        if is_team_member(after):

            await update_member_nickname(
                after
            )

        message = await find_team_message(
            after.guild
        )

        if message:

            try:

                await message.edit(
                    embed=build_team_embed(
                        after.guild
                    )
                )

            except discord.HTTPException:
                pass

    # --------------------------------------------------------
    # /team_panel
    # --------------------------------------------------------

    @app_commands.command(
        name="team_panel",
        description=(
            "Erstellt oder verschiebt "
            "die automatische Teamliste."
        ),
    )
    async def team_panel(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Bitte in einem Textkanal benutzen.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        existing = await find_team_message(
            interaction.guild
        )

        # Wenn bereits im selben Channel:
        # einfach aktualisieren
        if (
            existing
            and existing.channel.id
            == interaction.channel.id
        ):

            await existing.edit(
                embed=build_team_embed(
                    interaction.guild
                )
            )

            await interaction.followup.send(
                "✅ Teamliste wurde aktualisiert.",
                ephemeral=True,
            )

            return

        # Neue Teamliste posten
        new_message = await interaction.channel.send(
            embed=build_team_embed(
                interaction.guild
            )
        )

        # Alte Teamliste entfernen
        if existing:

            try:

                await existing.delete()

            except discord.HTTPException:
                pass

        await interaction.followup.send(
            (
                "✅ **Team-System eingerichtet**\n"
                f"📍 {new_message.channel.mention}"
            ),
            ephemeral=True,
        )

    # --------------------------------------------------------
    # /team_sync
    # --------------------------------------------------------

    @app_commands.command(
        name="team_sync",
        description=(
            "Synchronisiert Teamrollen, "
            "Nicknames und Teamliste."
        ),
    )
    async def team_sync(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        changed = await self.full_sync(
            interaction.guild
        )

        team_members = all_team_members(
            interaction.guild
        )

        await interaction.followup.send(
            (
                "✅ **TEAM-SYNC ABGESCHLOSSEN**\n\n"
                f"👥 Erkannte Teammitglieder: "
                f"**{len(team_members)}**\n"
                f"✏️ Nicknames geändert: "
                f"**{changed}**\n"
                "🔄 Teamliste aktualisiert"
            ),
            ephemeral=True,
        )

    # --------------------------------------------------------
    # /team_status
    # --------------------------------------------------------

    @app_commands.command(
        name="team_status",
        description=(
            "Zeigt den aktuellen Status "
            "des Team-Systems."
        ),
    )
    async def team_status(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        members = all_team_members(
            interaction.guild
        )

        absent = [
            member
            for member in members
            if member_is_absent(member)
        ]

        active = (
            len(members)
            - len(absent)
        )

        detected_roles = 0
        missing_roles = []

        for _, roles in TEAM_STRUCTURE:

            for role_name, _ in roles:

                if find_role(
                    interaction.guild,
                    role_name,
                ):

                    detected_roles += 1

                else:

                    missing_roles.append(
                        role_name
                    )

        embed = discord.Embed(
            title=(
                "⚙️ EHRP | SYSTEM • TEAM STATUS"
            ),
            description=(
                "## SYSTEM STATUS\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 **Teammitglieder:** "
                f"{len(members)}\n"
                f"🟢 **Aktiv:** "
                f"{active}\n"
                f"🏖️ **Abgemeldet:** "
                f"{len(absent)}\n\n"
                f"🎭 **Teamrollen erkannt:** "
                f"{detected_roles}\n"
                f"⚠️ **Fehlende Rollen:** "
                f"{len(missing_roles)}\n\n"
                "🔄 **Auto-Sync:** AKTIV\n"
                "⏱️ **Intervall:** 5 Minuten\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=(
                SUCCESS_COLOR
                if members
                else WARNING_COLOR
            ),
        )

        if missing_roles:

            embed.add_field(
                name="⚠️ Nicht gefundene Rollen",
                value=(
                    "\n".join(
                        f"• {role}"
                        for role
                        in missing_roles
                    )
                )[:1024],
                inline=False,
            )

        embed.set_footer(
            text="EHRP | System • Team Management"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        Team(bot)
    )
