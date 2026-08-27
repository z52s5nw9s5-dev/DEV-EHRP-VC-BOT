from __future__ import annotations

import re
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — TEAM SYSTEM
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C

TEAM_FOOTER = "EHRP_TEAM_SYSTEM_V5"


# ============================================================
# FESTE ROLLEN -> NAMETAG ZUORDNUNG
#
# WICHTIG:
# Nur EXAKTE Namen / Aliases werden erkannt.
# Dadurch wird z.B. "Fraktion Manager" NICHT zu Manager.
# ============================================================

TEAM_RANKS = [
    # LEITUNG
    {
        "section": "👑 Leitung",
        "name": "Founder",
        "tag": "[FD]",
        "aliases": [
            "Founder",
        ],
    },
    {
        "section": "👑 Leitung",
        "name": "Co-Founder",
        "tag": "[Co. FD]",
        "aliases": [
            "Co-Founder",
            "Co Founder",
        ],
    },

    # LEADEREBENE
    {
        "section": "⚜️ Leaderebene",
        "name": "Obervorstand",
        "tag": "[OVS]",
        "aliases": [
            "Obervorstand",
        ],
    },
    {
        "section": "⚜️ Leaderebene",
        "name": "Vorstand",
        "tag": "[VS]",
        "aliases": [
            "Vorstand",
        ],
    },
    {
        "section": "⚜️ Leaderebene",
        "name": "Sachbearbeiter",
        "tag": "[SB]",
        "aliases": [
            "Sachbearbeiter",
        ],
    },
    {
        "section": "⚜️ Leaderebene",
        "name": "Verwaltungsleitung",
        "tag": "[VL]",
        "aliases": [
            "Verwaltungsleitung",
            "Verwaltungs Leitung",
        ],
    },
    {
        "section": "⚜️ Leaderebene",
        "name": "Hauptverwaltung",
        "tag": "[HV]",
        "aliases": [
            "Hauptverwaltung",
            "Haupt Verwaltung",
        ],
    },

    # KERNTEAM
    {
        "section": "💎 Kernteam",
        "name": "Archivleitung",
        "tag": "[AL]",
        "aliases": [
            "Archivleitung",
            "Archiv Leitung",
        ],
    },
    {
        "section": "💎 Kernteam",
        "name": "Gesamtkoordinator",
        "tag": "[GT. K]",
        "aliases": [
            "Gesamtkoordinator",
            "Gesamt Koordinator",
        ],
    },
    {
        "section": "💎 Kernteam",
        "name": "Teamkoordinator",
        "tag": "[T. K]",
        "aliases": [
            "Teamkoordinator",
            "Team Koordinator",
        ],
    },
    {
        "section": "💎 Kernteam",
        "name": "Jr. Teamkoordinator",
        "tag": "[Jr. T. K]",
        "aliases": [
            "Jr. Teamkoordinator",
            "Jr Teamkoordinator",
            "Jr. Team Koordinator",
            "Junior Teamkoordinator",
        ],
    },

    # TEAMVERWALTUNG
    {
        "section": "🛡️ Teamverwaltung",
        "name": "Head of Management",
        "tag": "[HoM]",
        "aliases": [
            "Head of Management",
        ],
    },
    {
        "section": "🛡️ Teamverwaltung",
        "name": "Sr. Management",
        "tag": "[Sr. M]",
        "aliases": [
            "Sr. Management",
            "Sr Management",
            "Senior Management",
        ],
    },
    {
        "section": "🛡️ Teamverwaltung",
        "name": "Manager",
        "tag": "[M]",
        "aliases": [
            "Manager",
        ],
    },
    {
        "section": "🛡️ Teamverwaltung",
        "name": "Stv. Manager",
        "tag": "[Stv. M]",
        "aliases": [
            "Stv. Manager",
            "Stv Manager",
            "Stellv. Manager",
            "Stellvertretender Manager",
        ],
    },

    # MANAGEMENT
    {
        "section": "⚙️ Management",
        "name": "Admin-Koordinator",
        "tag": "[A. K]",
        "aliases": [
            "Admin-Koordinator",
            "Admin Koordinator",
        ],
    },
    {
        "section": "⚙️ Management",
        "name": "Systemadministrator",
        "tag": "[SYS. A]",
        "aliases": [
            "Systemadministrator",
            "System Administrator",
        ],
    },
    {
        "section": "⚙️ Management",
        "name": "Administrator",
        "tag": "[ADM]",
        "aliases": [
            "Administrator",
            "Admin",
        ],
    },
    {
        "section": "⚙️ Management",
        "name": "Jr. Administrator",
        "tag": "[Jr. ADM]",
        "aliases": [
            "Jr. Administrator",
            "Jr Administrator",
            "Jr. Admin",
            "Jr Admin",
            "Junior Administrator",
        ],
    },

    # ADMINISTRATION
    {
        "section": "🔨 Administration",
        "name": "Mod-Koordinator",
        "tag": "[MOD. K]",
        "aliases": [
            "Mod-Koordinator",
            "Mod Koordinator",
        ],
    },
    {
        "section": "🔨 Administration",
        "name": "Moderations-Spezialist",
        "tag": "[MOD. S]",
        "aliases": [
            "Moderations-Spezialist",
            "Moderations Spezialist",
        ],
    },
    {
        "section": "🔨 Administration",
        "name": "Moderator",
        "tag": "[MOD]",
        "aliases": [
            "Moderator",
        ],
    },
    {
        "section": "🔨 Administration",
        "name": "Jr. Moderator",
        "tag": "[Jr. MOD]",
        "aliases": [
            "Jr. Moderator",
            "Jr Moderator",
            "Junior Moderator",
        ],
    },

    # MODERATION / SUPPORT
    {
        "section": "🎧 Moderatoren",
        "name": "Sup-Koordinator",
        "tag": "[SUP. K]",
        "aliases": [
            "Sup-Koordinator",
            "Sup Koordinator",
            "Support-Koordinator",
            "Support Koordinator",
        ],
    },
    {
        "section": "🎧 Moderatoren",
        "name": "Support-Spezialist",
        "tag": "[SUP. S]",
        "aliases": [
            "Support-Spezialist",
            "Support Spezialist",
        ],
    },
    {
        "section": "🎧 Moderatoren",
        "name": "Supporter",
        "tag": "[SUP]",
        "aliases": [
            "Supporter",
        ],
    },
    {
        "section": "🎧 Moderatoren",
        "name": "Az. Supporter",
        "tag": "[Az. SUP]",
        "aliases": [
            "Az. Supporter",
            "Az Supporter",
            "Azubi Supporter",
        ],
    },
]


# ============================================================
# ABMELDUNG
# ============================================================

ABSENCE_WORDS = [
    "abgemeldet",
    "abwesen",
    "abwesenheit",
    "absence",
]


# ============================================================
# NORMALISIERUNG
# ============================================================

def normalize(text: str) -> str:
    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.casefold()

    # Unsichtbare Zeichen entfernen
    text = "".join(
        char
        for char in text
        if unicodedata.category(char)
        not in (
            "Cf",
            "Cc",
        )
    )

    # Discord-Deko entfernen:
    # » • ➡ ↪ | - usw.
    text = re.sub(
        r"[^a-z0-9äöüß]+",
        "",
        text,
    )

    return text


# ============================================================
# ROLLEN-MAP
# ============================================================

ROLE_MAP = {}

for rank in TEAM_RANKS:

    for alias in rank["aliases"]:

        ROLE_MAP[
            normalize(alias)
        ] = rank


# ============================================================
# ROLLE -> RANG
# ============================================================

def detect_rank_from_role(
    role: discord.Role,
):

    normalized = normalize(
        role.name
    )

    # NUR exakte Zuordnung!
    return ROLE_MAP.get(
        normalized
    )


# ============================================================
# HÖCHSTER TEAMRANG EINES USERS
# ============================================================

def get_member_rank(
    member: discord.Member,
):

    found = []

    for role in member.roles:

        rank = detect_rank_from_role(
            role
        )

        if rank is not None:

            found.append(
                rank
            )

    if not found:
        return None

    # TEAM_RANKS ist bereits von oben nach unten
    # sortiert -> höchster Rang gewinnt.

    for configured_rank in TEAM_RANKS:

        for member_rank in found:

            if (
                configured_rank["name"]
                == member_rank["name"]
            ):
                return configured_rank

    return None


# ============================================================
# TEAM MEMBER?
# ============================================================

def is_team_member(
    member: discord.Member,
) -> bool:

    return (
        get_member_rank(member)
        is not None
    )


# ============================================================
# ABGEMELDET?
# ============================================================

def is_absent(
    member: discord.Member,
) -> bool:

    for role in member.roles:

        name = normalize(
            role.name
        )

        for keyword in ABSENCE_WORDS:

            if normalize(keyword) in name:
                return True

    return False


# ============================================================
# ALLE NAMETAGS
# ============================================================

ALL_TAGS = sorted(
    {
        rank["tag"]
        for rank in TEAM_RANKS
    },
    key=len,
    reverse=True,
)


# ============================================================
# ALTEN NAMETAG ENTFERNEN
# ============================================================

def clean_nickname(
    member: discord.Member,
) -> str:

    name = (
        member.nick
        or member.global_name
        or member.name
    )

    # "- Abgemeldet" entfernen
    name = re.sub(
        r"\s*-\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # Bekannte Tags vorne entfernen
    for tag in ALL_TAGS:

        if name.casefold().startswith(
            tag.casefold()
        ):

            name = name[
                len(tag):
            ].strip()

            break

    return (
        name.strip()
        or member.name
    )


# ============================================================
# GEWÜNSCHTER NICKNAME
# ============================================================

def desired_nickname(
    member: discord.Member,
):

    rank = get_member_rank(
        member
    )

    if rank is None:
        return None

    base_name = clean_nickname(
        member
    )

    nickname = (
        f"{rank['tag']} "
        f"{base_name}"
    )

    if is_absent(
        member
    ):

        nickname += (
            " - Abgemeldet"
        )

    return nickname[:32]


# ============================================================
# NICKNAME SYNC
# ============================================================

async def sync_nickname(
    member: discord.Member,
) -> bool:

    if member.bot:
        return False

    guild = member.guild

    bot_member = guild.me

    if bot_member is None:
        return False

    # Discord erlaubt Owner-Nickname nicht
    if member.id == guild.owner_id:
        return False

    # Bot muss über der Rolle stehen
    if (
        member.top_role
        >= bot_member.top_role
    ):
        print(
            "⚠️ Kann Nickname nicht ändern: "
            f"{member.display_name}"
        )

        return False

    rank = get_member_rank(
        member
    )

    # ========================================================
    # USER IST NICHT MEHR IM TEAM
    # ========================================================

    if rank is None:

        if member.nick is None:
            return False

        cleaned = clean_nickname(
            member
        )

        if cleaned == member.nick:
            return False

        try:

            await member.edit(
                nick=cleaned[:32],
                reason=(
                    "EHRP | System "
                    "Teamrang entfernt"
                ),
            )

            return True

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):

            return False

    # ========================================================
    # USER IST TEAM
    # ========================================================

    wanted = desired_nickname(
        member
    )

    if wanted is None:
        return False

    if member.nick == wanted:
        return False

    try:

        await member.edit(
            nick=wanted,
            reason=(
                "EHRP | System "
                f"Nametag {rank['tag']}"
            ),
        )

        print(
            "✅ TEAM TAG: "
            f"{member.name} -> {wanted}"
        )

        return True

    except discord.Forbidden:

        print(
            "❌ Keine Nickname-Rechte: "
            f"{member.name}"
        )

    except discord.HTTPException as error:

        print(
            "❌ Nickname Fehler: "
            f"{member.name}: {error}"
        )

    return False


# ============================================================
# TEAMMITGLIEDER
# ============================================================

def all_team_members(
    guild: discord.Guild,
):

    return [
        member
        for member in guild.members
        if (
            not member.bot
            and get_member_rank(member)
            is not None
        )
    ]


# ============================================================
# MITGLIEDER PRO RANG
# ============================================================

def members_for_rank(
    guild: discord.Guild,
    wanted_rank: dict,
):

    members = []

    for member in guild.members:

        if member.bot:
            continue

        rank = get_member_rank(
            member
        )

        if rank is None:
            continue

        if (
            rank["name"]
            == wanted_rank["name"]
        ):

            members.append(
                member
            )

    members.sort(
        key=lambda m:
        m.display_name.casefold()
    )

    return members


# ============================================================
# ALLE ERKANNTEN SERVERROLLEN
# ============================================================

def mapped_server_roles(
    guild: discord.Guild,
):

    result = []

    for role in reversed(
        guild.roles
    ):

        rank = detect_rank_from_role(
            role
        )

        if rank is None:
            continue

        result.append(
            (
                role,
                rank,
            )
        )

    return result


# ============================================================
# TEAM PANEL
# ============================================================

def build_team_embed(
    guild: discord.Guild,
):

    members = all_team_members(
        guild
    )

    absent = sum(
        1
        for member in members
        if is_absent(member)
    )

    embed = discord.Embed(
        title=(
            "👥 EHRP | SYSTEM • TEAMLISTE"
        ),
        description=(
            "## OFFIZIELLE TEAMÜBERSICHT\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** "
            f"{len(members)}\n"
            f"🟢 **Aktiv:** "
            f"{len(members) - absent}\n"
            f"🏖️ **Abgemeldet:** "
            f"{absent}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SYSTEM_COLOR,
    )

    sections = []

    for rank in TEAM_RANKS:

        if (
            rank["section"]
            not in sections
        ):

            sections.append(
                rank["section"]
            )

    for section in sections:

        lines = []

        section_ranks = [
            rank
            for rank in TEAM_RANKS
            if rank["section"]
            == section
        ]

        for rank in section_ranks:

            members_here = members_for_rank(
                guild,
                rank,
            )

            if members_here:

                names = []

                for member in members_here:

                    state = (
                        "🏖️"
                        if is_absent(member)
                        else "🟢"
                    )

                    names.append(
                        f"{state} {member.mention}"
                    )

                member_text = "\n".join(
                    names
                )

            else:

                member_text = "—"

            lines.append(
                (
                    f"**{rank['tag']} "
                    f"{rank['name']}**\n"
                    f"{member_text}"
                )
            )

        embed.add_field(
            name=section,
            value="\n\n".join(
                lines
            )[:1024],
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{TEAM_FOOTER} • "
            "Automatische Synchronisierung"
        )
    )

    return embed


# ============================================================
# TEAM PANEL FINDEN
# ============================================================

async def find_team_panel(
    guild: discord.Guild,
):

    if guild.me is None:
        return None

    for channel in guild.text_channels:

        permissions = (
            channel.permissions_for(
                guild.me
            )
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
                    != guild.me.id
                ):
                    continue

                if not message.embeds:
                    continue

                footer = (
                    message.embeds[0]
                    .footer.text
                    or ""
                )

                if TEAM_FOOTER in footer:

                    return message

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):

            continue

    return None


# ============================================================
# FULL SYNC
# ============================================================

async def full_sync(
    guild: discord.Guild,
):

    changed = 0

    for member in guild.members:

        if member.bot:
            continue

        if await sync_nickname(
            member
        ):

            changed += 1

    panel = await find_team_panel(
        guild
    )

    if panel is not None:

        try:

            await panel.edit(
                embed=build_team_embed(
                    guild
                )
            )

        except discord.HTTPException:

            pass

    return changed


# ============================================================
# ACCESS
# ============================================================

async def ensure_dev(
    interaction: discord.Interaction,
) -> bool:

    if (
        interaction.guild is None
        or not isinstance(
            interaction.user,
            discord.Member,
        )
    ):

        await interaction.response.send_message(
            "❌ Nur auf dem Server verfügbar.",
            ephemeral=True,
        )

        return False

    if (
        interaction.user
        .guild_permissions
        .administrator
    ):

        return True

    try:

        role_id = int(
            DEV_ROLE_ID
        )

    except (
        ValueError,
        TypeError,
    ):

        role_id = 0

    dev_role = (
        interaction.guild.get_role(
            role_id
        )
    )

    if (
        dev_role is not None
        and dev_role
        in interaction.user.roles
    ):

        return True

    await interaction.response.send_message(
        "❌ Keine Berechtigung.",
        ephemeral=True,
    )

    return False


# ============================================================
# COG
# ============================================================

class Team(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot

        self.auto_sync.start()


    def cog_unload(
        self,
    ):

        self.auto_sync.cancel()


    # ========================================================
    # AUTO SYNC
    # ========================================================

    @tasks.loop(
        minutes=5
    )
    async def auto_sync(
        self,
    ):

        for guild in self.bot.guilds:

            try:

                await full_sync(
                    guild
                )

            except Exception as error:

                print(
                    "❌ Team Auto-Sync: "
                    f"{error}"
                )


    @auto_sync.before_loop
    async def before_auto_sync(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # ROLLENÄNDERUNG -> SOFORT TAG ÄNDERN
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):

        if (
            before.roles
            == after.roles
            and before.nick
            == after.nick
        ):

            return

        try:

            await sync_nickname(
                after
            )

            panel = (
                await find_team_panel(
                    after.guild
                )
            )

            if panel:

                await panel.edit(
                    embed=build_team_embed(
                        after.guild
                    )
                )

        except Exception as error:

            print(
                "❌ Team Member Update: "
                f"{error}"
            )


    # ========================================================
    # /team_map
    #
    # DAS IST JETZT DER WICHTIGE BEFEHL:
    #
    # echte Rolle -> Nametag
    # ========================================================

    @app_commands.command(
        name="team_map",
        description=(
            "Zeigt jede erkannte Teamrolle "
            "und den zugehörigen Nametag."
        ),
    )
    async def team_map(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):

            return

        mapped = mapped_server_roles(
            interaction.guild
        )

        lines = []

        for role, rank in mapped:

            lines.append(
                (
                    f"🎭 `{role.name}`\n"
                    f"↳ **{rank['tag']} "
                    f"{rank['name']}**"
                )
            )

        embed = discord.Embed(
            title=(
                "🔎 EHRP | ROLE → NAMETAG"
            ),
            description=(
                "\n\n".join(
                    lines
                )[:4000]
                if lines
                else (
                    "❌ Keine Teamrollen "
                    "wurden erkannt."
                )
            ),
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text=(
                "Nur exakt definierte "
                "Teamrollen werden verwendet."
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_status
    # ========================================================

    @app_commands.command(
        name="team_status",
        description=(
            "Zeigt den Status "
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

        absent = sum(
            1
            for member in members
            if is_absent(member)
        )

        mapped = mapped_server_roles(
            interaction.guild
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
                f"{len(members) - absent}\n"
                f"🏖️ **Abgemeldet:** "
                f"{absent}\n\n"
                f"🎭 **Serverrollen erkannt:** "
                f"{len(mapped)}\n"
                f"🏷️ **Nametag-Regeln:** "
                f"{len(TEAM_RANKS)}\n\n"
                "🔄 **Auto-Sync:** AKTIV\n"
                "⏱️ **Intervall:** 5 Minuten\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=SUCCESS_COLOR,
        )

        embed.set_footer(
            text=(
                "EHRP | System • "
                "Team Management V5"
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_sync
    # ========================================================

    @app_commands.command(
        name="team_sync",
        description=(
            "Synchronisiert alle "
            "Team-Nametags."
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

        changed = await full_sync(
            interaction.guild
        )

        members = all_team_members(
            interaction.guild
        )

        await interaction.followup.send(
            (
                "✅ **TEAM-SYNC FERTIG**\n\n"
                f"👥 Teammitglieder erkannt: "
                f"**{len(members)}**\n"
                f"✏️ Nametags geändert: "
                f"**{changed}**\n\n"
                "Nutze `/team_map`, "
                "um Rolle → Nametag zu prüfen."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /team_panel
    # ========================================================

    @app_commands.command(
        name="team_panel",
        description=(
            "Erstellt die automatische "
            "Teamliste."
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
                "❌ Bitte in einem "
                "Textkanal benutzen.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        old_panel = (
            await find_team_panel(
                interaction.guild
            )
        )

        if (
            old_panel
            and old_panel.channel.id
            == interaction.channel.id
        ):

            await old_panel.edit(
                embed=build_team_embed(
                    interaction.guild
                )
            )

            await interaction.followup.send(
                "✅ Teamliste aktualisiert.",
                ephemeral=True,
            )

            return

        message = (
            await interaction.channel.send(
                embed=build_team_embed(
                    interaction.guild
                )
            )
        )

        if old_panel:

            try:

                await old_panel.delete()

            except discord.HTTPException:

                pass

        await interaction.followup.send(
            (
                "✅ **Teamliste erstellt**\n"
                f"📍 {message.channel.mention}"
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
        Team(bot)
    )
