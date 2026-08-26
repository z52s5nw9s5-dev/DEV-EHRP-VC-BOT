from __future__ import annotations

import re
import unicodedata

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — TEAM CONFIG
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

TEAM_FOOTER_MARKER = "EHRP_TEAM_SYSTEM_V3"


# ============================================================
# TEAMSTRUKTUR + DEINE KÜRZEL
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
        "🎧 Moderatoren",
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
    "abwesenheit",
    "absence",
)


# ============================================================
# DEV CHECK
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
            "❌ Dieser Befehl funktioniert nur auf dem Server.",
            ephemeral=True,
        )
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    try:
        dev_role_id = int(DEV_ROLE_ID)
    except (TypeError, ValueError):
        dev_role_id = 0

    dev_role = interaction.guild.get_role(
        dev_role_id
    )

    if (
        dev_role is not None
        and dev_role in interaction.user.roles
    ):
        return True

    await interaction.response.send_message(
        "❌ Du darfst diese Systemfunktion nicht benutzen.",
        ephemeral=True,
    )

    return False


# ============================================================
# ROBUSTE ROLLEN-NORMALISIERUNG
# ============================================================

def normalize_role_name(
    value: str,
) -> str:

    # Unicode vereinheitlichen
    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    value = value.casefold()

    # unsichtbare Unicode-Zeichen entfernen
    value = "".join(
        char
        for char in value
        if unicodedata.category(char)
        not in (
            "Cf",
            "Cc",
        )
    )

    # alles außer Buchstaben/Zahlen wird Leerzeichen
    value = re.sub(
        r"[^a-z0-9äöüß]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def compact_role_name(
    value: str,
) -> str:

    return normalize_role_name(
        value
    ).replace(" ", "")


# ============================================================
# FLACHE RANGLISTE
# ============================================================

def all_rank_entries():
    entries = []

    for section, roles in TEAM_STRUCTURE:
        for role_name, prefix in roles:
            entries.append(
                {
                    "section": section,
                    "role_name": role_name,
                    "prefix": prefix,
                    "normal": normalize_role_name(
                        role_name
                    ),
                    "compact": compact_role_name(
                        role_name
                    ),
                }
            )

    # längste Namen zuerst
    # verhindert z.B. Administrator statt Jr. Administrator
    entries.sort(
        key=lambda item: len(
            item["compact"]
        ),
        reverse=True,
    )

    return entries


RANK_ENTRIES = all_rank_entries()


# ============================================================
# ROLLE ERKENNEN
# ============================================================

def match_known_rank(
    discord_role_name: str,
):

    role_normal = normalize_role_name(
        discord_role_name
    )

    role_compact = compact_role_name(
        discord_role_name
    )

    if not role_compact:
        return None

    # 1. exakter Match
    for entry in RANK_ENTRIES:

        if (
            role_normal == entry["normal"]
            or role_compact == entry["compact"]
        ):
            return entry

    # 2. Rollenname kann vorne Server-Deko/Text enthalten
    # Beispiel:
    # "team obervorstand"
    # "ehrp jr administrator"
    #
    # längste Rangnamen werden zuerst geprüft
    for entry in RANK_ENTRIES:

        target_normal = entry["normal"]
        target_compact = entry["compact"]

        if role_normal.endswith(
            " " + target_normal
        ):
            return entry

        if role_compact.endswith(
            target_compact
        ):
            # Schutz vor gefährlichen Teilmatches
            #
            # Administrator soll NICHT
            # Systemadministrator matchen,
            # da Systemadministrator vorher
            # als längerer Rank geprüft wurde.

            return entry

    return None


def find_discord_role(
    guild: discord.Guild,
    rank_name: str,
):

    wanted_entry = None

    for entry in RANK_ENTRIES:

        if entry["role_name"] == rank_name:
            wanted_entry = entry
            break

    if wanted_entry is None:
        return None

    matches = []

    for role in guild.roles:

        detected = match_known_rank(
            role.name
        )

        if (
            detected
            and detected["role_name"]
            == wanted_entry["role_name"]
        ):
            matches.append(
                role
            )

    if not matches:
        return None

    # höchste Discord-Rolle verwenden
    matches.sort(
        key=lambda role: role.position,
        reverse=True,
    )

    return matches[0]


# ============================================================
# TEAMRANG EINES MEMBERS
# ============================================================

def get_member_team_rank(
    member: discord.Member,
):

    matches = []

    for role in member.roles:

        detected = match_known_rank(
            role.name
        )

        if detected:

            matches.append(
                {
                    **detected,
                    "discord_role": role,
                }
            )

    if not matches:
        return None

    # Reihenfolge aus TEAM_STRUCTURE bestimmt,
    # welcher Rang höher ist.
    priority = {}

    index = 0

    for section, roles in TEAM_STRUCTURE:

        for role_name, _ in roles:

            priority[
                role_name
            ] = index

            index += 1

    matches.sort(
        key=lambda item: priority.get(
            item["role_name"],
            9999,
        )
    )

    return matches[0]


def is_team_member(
    member: discord.Member,
) -> bool:

    return (
        get_member_team_rank(
            member
        )
        is not None
    )


# ============================================================
# ABWESENHEIT
# ============================================================

def member_is_absent(
    member: discord.Member,
) -> bool:

    for role in member.roles:

        normalized = normalize_role_name(
            role.name
        )

        compact = normalized.replace(
            " ",
            ""
        )

        for keyword in ABSENCE_KEYWORDS:

            keyword_compact = keyword.replace(
                " ",
                ""
            )

            if keyword_compact in compact:
                return True

    return False


# ============================================================
# NICKNAME CLEANUP
# ============================================================

def remove_team_prefix(
    name: str,
) -> str:

    name = name.strip()

    # Abgemeldet entfernen
    name = re.sub(
        r"\s*[-|•]\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # bekannte Kürzel entfernen
    all_prefixes = []

    for _, roles in TEAM_STRUCTURE:

        for _, prefix in roles:

            all_prefixes.append(
                prefix
            )

    all_prefixes.sort(
        key=len,
        reverse=True,
    )

    for prefix in all_prefixes:

        if name.lower().startswith(
            prefix.lower()
        ):

            name = name[
                len(prefix):
            ].strip()

            break

    return (
        name.strip()
        or "User"
    )


def base_member_name(
    member: discord.Member,
) -> str:

    current_name = (
        member.nick
        or member.global_name
        or member.name
    )

    cleaned = remove_team_prefix(
        current_name
    )

    return (
        cleaned
        or member.name
    )


def desired_team_nickname(
    member: discord.Member,
):

    rank = get_member_team_rank(
        member
    )

    if rank is None:
        return None

    name = base_member_name(
        member
    )

    new_name = (
        f"{rank['prefix']} {name}"
    )

    if member_is_absent(
        member
    ):
        new_name += " - Abgemeldet"

    return new_name[:32]


# ============================================================
# NICKNAME ÄNDERN
# ============================================================

async def sync_member_nickname(
    member: discord.Member,
) -> bool:

    if member.bot:
        return False

    rank = get_member_team_rank(
        member
    )

    # Mitglied ist kein Teammitglied mehr
    if rank is None:

        if member.nick is None:
            return False

        cleaned = remove_team_prefix(
            member.nick
        )

        if cleaned == member.nick:
            return False

        bot_member = member.guild.me

        if bot_member is None:
            return False

        if member.id == member.guild.owner_id:
            return False

        if (
            member.top_role
            >= bot_member.top_role
        ):
            return False

        try:

            await member.edit(
                nick=cleaned[:32],
                reason=(
                    "EHRP | System "
                    "Teamrolle entfernt"
                ),
            )

            return True

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            return False

    desired = desired_team_nickname(
        member
    )

    if not desired:
        return False

    if member.nick == desired:
        return False

    bot_member = member.guild.me

    if bot_member is None:
        return False

    if member.id == member.guild.owner_id:
        return False

    if (
        member.top_role
        >= bot_member.top_role
    ):
        print(
            "⚠️ Nickname nicht änderbar: "
            f"{member} | Bot-Rolle zu niedrig"
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

        print(
            f"✅ Nickname: {member} -> {desired}"
        )

        return True

    except discord.Forbidden:

        print(
            "⚠️ Keine Berechtigung "
            f"für Nickname von {member}"
        )

    except discord.HTTPException as error:

        print(
            f"❌ Nickname Fehler "
            f"{member}: {error}"
        )

    return False


# ============================================================
# ALLE TEAMMITGLIEDER
# ============================================================

def get_all_team_members(
    guild: discord.Guild,
):

    members = []

    for member in guild.members:

        if member.bot:
            continue

        rank = get_member_team_rank(
            member
        )

        if rank:

            members.append(
                member
            )

    return members


def members_for_rank(
    guild: discord.Guild,
    rank_name: str,
):

    members = []

    for member in guild.members:

        if member.bot:
            continue

        rank = get_member_team_rank(
            member
        )

        if (
            rank
            and rank["role_name"]
            == rank_name
        ):

            members.append(
                member
            )

    members.sort(
        key=lambda member:
        member.display_name.casefold()
    )

    return members


# ============================================================
# TEAMLISTE
# ============================================================

def build_team_embed(
    guild: discord.Guild,
):

    members = get_all_team_members(
        guild
    )

    absent_count = sum(
        1
        for member in members
        if member_is_absent(member)
    )

    active_count = (
        len(members)
        - absent_count
    )

    embed = discord.Embed(
        title="👥 EHRP | SYSTEM • TEAMLISTE",
        description=(
            "## OFFIZIELLE TEAMÜBERSICHT\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** {len(members)}\n"
            f"🟢 **Aktiv:** {active_count}\n"
            f"🏖️ **Abgemeldet:** {absent_count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Die Liste wird automatisch "
            "mit den Serverrollen synchronisiert."
        ),
        color=SYSTEM_COLOR,
    )

    for section_name, roles in TEAM_STRUCTURE:

        lines = []

        for role_name, prefix in roles:

            rank_members = members_for_rank(
                guild,
                role_name,
            )

            if rank_members:

                member_lines = []

                for member in rank_members:

                    status = (
                        "🏖️"
                        if member_is_absent(member)
                        else "🟢"
                    )

                    member_lines.append(
                        f"{status} {member.mention}"
                    )

                members_text = "\n".join(
                    member_lines
                )

            else:

                members_text = "—"

            lines.append(
                f"**{prefix} {role_name}**\n"
                f"{members_text}"
            )

        embed.add_field(
            name=section_name,
            value="\n\n".join(
                lines
            )[:1024],
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
# TEAM MESSAGE FINDEN
# ============================================================

async def find_team_message(
    guild: discord.Guild,
):

    bot_member = guild.me

    if bot_member is None:
        return None

    for channel in guild.text_channels:

        permissions = channel.permissions_for(
            bot_member
        )

        if not (
            permissions.view_channel
            and permissions.read_message_history
        ):
            continue

        try:

            async for message in channel.history(
                limit=75
            ):

                if (
                    message.author.id
                    != bot_member.id
                ):
                    continue

                if not message.embeds:
                    continue

                footer = (
                    message.embeds[0]
                    .footer.text
                    or ""
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
# FULL SYNC
# ============================================================

async def perform_full_sync(
    guild: discord.Guild,
):

    changed = 0

    # Absichtlich alle User prüfen.
    # Dadurch werden alte Team-Kürzel auch entfernt,
    # wenn eine Teamrolle entzogen wurde.
    for member in guild.members:

        if member.bot:
            continue

        if await sync_member_nickname(
            member
        ):
            changed += 1

    team_message = await find_team_message(
        guild
    )

    if team_message:

        try:

            await team_message.edit(
                embed=build_team_embed(
                    guild
                )
            )

        except discord.HTTPException as error:

            print(
                "❌ Teamliste konnte nicht "
                f"aktualisiert werden: {error}"
            )

    return changed


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


    # ========================================================
    # AUTOMATISCH ALLE 5 MINUTEN
    # ========================================================

    @tasks.loop(
        minutes=5
    )
    async def team_sync_loop(
        self,
    ):

        for guild in self.bot.guilds:

            try:

                await perform_full_sync(
                    guild
                )

            except Exception as error:

                print(
                    "❌ Team Auto-Sync Fehler "
                    f"{guild.name}: {error}"
                )


    @team_sync_loop.before_loop
    async def before_team_sync_loop(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # SOFORT BEI ROLLENÄNDERUNG
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):

        # Wir reagieren nur auf relevante Änderungen
        if (
            before.roles == after.roles
            and before.nick == after.nick
        ):
            return

        try:

            await sync_member_nickname(
                after
            )

            team_message = await find_team_message(
                after.guild
            )

            if team_message:

                await team_message.edit(
                    embed=build_team_embed(
                        after.guild
                    )
                )

        except Exception as error:

            print(
                "❌ Member Update Fehler: "
                f"{error}"
            )


    # ========================================================
    # /team_sync
    # ========================================================

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

        changed = await perform_full_sync(
            interaction.guild
        )

        members = get_all_team_members(
            interaction.guild
        )

        absent = sum(
            1
            for member in members
            if member_is_absent(
                member
            )
        )

        await interaction.followup.send(
            (
                "✅ **TEAM-SYNC ABGESCHLOSSEN**\n\n"
                f"👥 Teammitglieder erkannt: "
                f"**{len(members)}**\n"
                f"🟢 Aktiv: "
                f"**{len(members) - absent}**\n"
                f"🏖️ Abgemeldet: "
                f"**{absent}**\n"
                f"✏️ Nicknames geändert: "
                f"**{changed}**"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /team_status
    # ========================================================

    @app_commands.command(
        name="team_status",
        description=(
            "Zeigt den Status des Team-Systems."
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

        members = get_all_team_members(
            interaction.guild
        )

        absent = sum(
            1
            for member in members
            if member_is_absent(
                member
            )
        )

        detected_roles = []
        missing_roles = []

        for _, roles in TEAM_STRUCTURE:

            for role_name, _ in roles:

                discord_role = find_discord_role(
                    interaction.guild,
                    role_name,
                )

                if discord_role:

                    detected_roles.append(
                        (
                            role_name,
                            discord_role.name,
                        )
                    )

                else:

                    missing_roles.append(
                        role_name
                    )

        embed = discord.Embed(
            title="⚙️ EHRP | SYSTEM • TEAM STATUS",
            description=(
                "## SYSTEM STATUS\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 **Teammitglieder:** "
                f"{len(members)}\n"
                f"🟢 **Aktiv:** "
                f"{len(members) - absent}\n"
                f"🏖️ **Abgemeldet:** "
                f"{absent}\n\n"
                f"🎭 **Teamrollen erkannt:** "
                f"{len(detected_roles)} / "
                f"{len(RANK_ENTRIES)}\n"
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
                value="\n".join(
                    f"• {role}"
                    for role in missing_roles
                )[:1024],
                inline=False,
            )

        embed.set_footer(
            text=(
                "EHRP | System • "
                "Team Management V3"
            )
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_debug
    # ========================================================

    @app_commands.command(
        name="team_debug",
        description=(
            "Zeigt, welche Serverrollen "
            "das Team-System erkennt."
        ),
    )
    async def team_debug(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        detected = []

        for role in reversed(
            interaction.guild.roles
        ):

            rank = match_known_rank(
                role.name
            )

            if not rank:
                continue

            detected.append(
                (
                    f"`{role.name}`\n"
                    f"↳ **{rank['prefix']} "
                    f"{rank['role_name']}**"
                )
            )

        embed = discord.Embed(
            title="🔎 EHRP | TEAM DEBUG",
            description=(
                "Hier siehst du, welche echten "
                "Discord-Rollen erkannt werden.\n\n"
                + (
                    "\n\n".join(
                        detected
                    )[:4000]
                    if detected
                    else "❌ Keine Teamrollen erkannt."
                )
            ),
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text="EHRP | System • Role Detection"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_panel
    # ========================================================

    @app_commands.command(
        name="team_panel",
        description=(
            "Erstellt die automatische Teamliste "
            "im aktuellen Channel."
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
                "❌ Bitte benutze den Befehl "
                "in einem Textkanal.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        old_message = await find_team_message(
            interaction.guild
        )

        # gleiche Nachricht aktualisieren
        if (
            old_message
            and old_message.channel.id
            == interaction.channel.id
        ):

            await old_message.edit(
                embed=build_team_embed(
                    interaction.guild
                )
            )

            await interaction.followup.send(
                "✅ Teamliste aktualisiert.",
                ephemeral=True,
            )

            return

        new_message = await interaction.channel.send(
            embed=build_team_embed(
                interaction.guild
            )
        )

        # alte Teamliste entfernen
        if old_message:

            try:

                await old_message.delete()

            except discord.HTTPException:
                pass

        await interaction.followup.send(
            (
                "✅ **Team-Panel erstellt**\n"
                f"📍 {new_message.channel.mention}"
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
