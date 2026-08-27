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

TEAM_FOOTER_MARKER = "EHRP_TEAM_SYSTEM_V4"


# ============================================================
# TEAMSTRUKTUR + KÜRZEL
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


# ============================================================
# ROLLEN, DIE KOMPLETT IGNORIERT WERDEN
# ============================================================

IGNORED_ROLE_NAMES = (
    "fraktion manager",
    "fraktions manager",
    "fraktionsmanager",
    "fraktion verwaltung",
    "stv fraktion verwaltung",
    "fraktions verwaltung",
    "fraktions ebene",
    "developmentleitung",
    "development",
    "jr development",
    "team ausbilder",
    "team ausbilder leitung",
    "ausbildungs ebene",
    "in game rechte",
    "bau rechte",
)


ABSENCE_KEYWORDS = (
    "abgemeldet",
    "abwesen",
    "abwesenheit",
    "absence",
)


# ============================================================
# ACCESS
# ============================================================

async def ensure_dev(
    interaction: discord.Interaction,
) -> bool:

    if (
        interaction.guild is None
        or not isinstance(interaction.user, discord.Member)
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

    dev_role = interaction.guild.get_role(dev_role_id)

    if dev_role is not None and dev_role in interaction.user.roles:
        return True

    await interaction.response.send_message(
        "❌ Du darfst diese Systemfunktion nicht benutzen.",
        ephemeral=True,
    )

    return False


# ============================================================
# NORMALISIERUNG
# ============================================================

def normalize_role_name(value: str) -> str:

    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()

    value = "".join(
        char
        for char in value
        if unicodedata.category(char) not in ("Cf", "Cc")
    )

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


def compact_role_name(value: str) -> str:
    return normalize_role_name(value).replace(" ", "")


# ============================================================
# IGNORE CHECK
# ============================================================

def role_is_ignored(role_name: str) -> bool:

    normal = normalize_role_name(role_name)
    compact = compact_role_name(role_name)

    for ignored in IGNORED_ROLE_NAMES:

        ignored_normal = normalize_role_name(ignored)
        ignored_compact = compact_role_name(ignored)

        if (
            normal == ignored_normal
            or compact == ignored_compact
        ):
            return True

    return False


# ============================================================
# RANK ENTRIES
# ============================================================

def build_rank_entries():
    entries = []

    for section, roles in TEAM_STRUCTURE:

        for role_name, prefix in roles:

            entries.append(
                {
                    "section": section,
                    "role_name": role_name,
                    "prefix": prefix,
                    "normal": normalize_role_name(role_name),
                    "compact": compact_role_name(role_name),
                }
            )

    entries.sort(
        key=lambda item: len(item["compact"]),
        reverse=True,
    )

    return entries


RANK_ENTRIES = build_rank_entries()


# ============================================================
# ALIASES
# ============================================================

ROLE_ALIASES = {
    "archiv leitung": "Archivleitung",
    "archivleitung": "Archivleitung",

    "administrator": "Administrator",
    "admin": "Administrator",

    "jr administrator": "Jr. Administrator",
    "jr admin": "Jr. Administrator",
    "junior administrator": "Jr. Administrator",
    "junior admin": "Jr. Administrator",

    "system administrator": "Systemadministrator",

    "admin koordinator": "Admin-Koordinator",

    "mod koordinator": "Mod-Koordinator",

    "moderations spezialist": "Moderations-Spezialist",

    "support spezialist": "Support-Spezialist",

    "sup koordinator": "Sup-Koordinator",

    "co founder": "Co-Founder",

    "jr teamkoordinator": "Jr. Teamkoordinator",

    "jr moderator": "Jr. Moderator",

    "az supporter": "Az. Supporter",

    "stv manager": "Stv. Manager",

    "sr management": "Sr. Management",

    "head of management": "Head of Management",
}


# ============================================================
# MATCH RANK
# ============================================================

def get_entry_by_rank_name(rank_name: str):

    for entry in RANK_ENTRIES:

        if entry["role_name"] == rank_name:
            return entry

    return None


def match_known_rank(
    discord_role_name: str,
):

    # Fraktion Manager & Co. komplett raus
    if role_is_ignored(discord_role_name):
        return None

    role_normal = normalize_role_name(
        discord_role_name
    )

    role_compact = compact_role_name(
        discord_role_name
    )

    if not role_compact:
        return None

    # --------------------------------------------------------
    # 1. EXAKT
    # --------------------------------------------------------

    for entry in RANK_ENTRIES:

        if (
            role_normal == entry["normal"]
            or role_compact == entry["compact"]
        ):
            return entry

    # --------------------------------------------------------
    # 2. ALIAS
    # --------------------------------------------------------

    for alias, target_rank in ROLE_ALIASES.items():

        alias_normal = normalize_role_name(
            alias
        )

        alias_compact = compact_role_name(
            alias
        )

        if (
            role_normal == alias_normal
            or role_compact == alias_compact
        ):
            return get_entry_by_rank_name(
                target_rank
            )

    # --------------------------------------------------------
    # 3. NUR DEKO VOR DEM RANG ERLAUBEN
    # --------------------------------------------------------

    for entry in RANK_ENTRIES:

        target = entry["normal"]

        pattern = (
            r"(?:^|\s)"
            + re.escape(target)
            + r"$"
        )

        if re.search(
            pattern,
            role_normal,
        ):
            return entry

    return None


# ============================================================
# DISCORD ROLE FINDEN
# ============================================================

def find_discord_role(
    guild: discord.Guild,
    rank_name: str,
):

    found = []

    for role in guild.roles:

        detected = match_known_rank(
            role.name
        )

        if (
            detected is not None
            and detected["role_name"] == rank_name
        ):
            found.append(
                role
            )

    if not found:
        return None

    found.sort(
        key=lambda role: role.position,
        reverse=True,
    )

    return found[0]


# ============================================================
# MEMBER RANK
# ============================================================

def get_member_team_rank(
    member: discord.Member,
):

    detected_ranks = []

    for role in member.roles:

        detected = match_known_rank(
            role.name
        )

        if detected is None:
            continue

        detected_ranks.append(
            {
                **detected,
                "discord_role": role,
            }
        )

    if not detected_ranks:
        return None

    priority = {}

    index = 0

    for _, roles in TEAM_STRUCTURE:

        for role_name, _ in roles:

            priority[role_name] = index
            index += 1

    detected_ranks.sort(
        key=lambda item: priority.get(
            item["role_name"],
            9999,
        )
    )

    return detected_ranks[0]


def is_team_member(
    member: discord.Member,
) -> bool:

    return (
        get_member_team_rank(member)
        is not None
    )


# ============================================================
# ABSENCE
# ============================================================

def member_is_absent(
    member: discord.Member,
) -> bool:

    for role in member.roles:

        normalized = normalize_role_name(
            role.name
        )

        for keyword in ABSENCE_KEYWORDS:

            if keyword in normalized:
                return True

    return False


# ============================================================
# NICKNAME CLEANER
# ============================================================

def all_prefixes():
    prefixes = []

    for _, roles in TEAM_STRUCTURE:

        for _, prefix in roles:

            prefixes.append(
                prefix
            )

    prefixes.sort(
        key=len,
        reverse=True,
    )

    return prefixes


TEAM_PREFIXES = all_prefixes()


def clean_member_name(
    member: discord.Member,
) -> str:

    name = (
        member.nick
        or member.global_name
        or member.name
    )

    # Abgemeldet hinten entfernen
    name = re.sub(
        r"\s*-\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    # bekannten Team-Prefix entfernen
    for prefix in TEAM_PREFIXES:

        if name.casefold().startswith(
            prefix.casefold()
        ):
            name = name[
                len(prefix):
            ].strip()

            break

    return (
        name.strip()
        or member.name
    )


def desired_nickname(
    member: discord.Member,
):

    rank = get_member_team_rank(
        member
    )

    if rank is None:
        return None

    base = clean_member_name(
        member
    )

    nickname = (
        f"{rank['prefix']} {base}"
    )

    if member_is_absent(
        member
    ):
        nickname += " - Abgemeldet"

    return nickname[:32]


# ============================================================
# NICKNAME SYNC
# ============================================================

async def sync_member_nickname(
    member: discord.Member,
) -> bool:

    if member.bot:
        return False

    guild = member.guild
    bot_member = guild.me

    if bot_member is None:
        return False

    if member.id == guild.owner_id:
        return False

    if member.top_role >= bot_member.top_role:
        return False

    rank = get_member_team_rank(
        member
    )

    # --------------------------------------------------------
    # KEIN TEAM MEHR
    # --------------------------------------------------------

    if rank is None:

        if not member.nick:
            return False

        cleaned = clean_member_name(
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

    # --------------------------------------------------------
    # TEAM
    # --------------------------------------------------------

    desired = desired_nickname(
        member
    )

    if not desired:
        return False

    if member.nick == desired:
        return False

    try:

        await member.edit(
            nick=desired,
            reason=(
                "EHRP | System "
                "Team-Nickname synchronisiert"
            ),
        )

        return True

    except discord.Forbidden:

        print(
            f"⚠️ Nickname nicht erlaubt: {member}"
        )

    except discord.HTTPException as error:

        print(
            f"❌ Nickname Fehler {member}: {error}"
        )

    return False


# ============================================================
# TEAM MEMBERS
# ============================================================

def get_all_team_members(
    guild: discord.Guild,
):

    members = []

    for member in guild.members:

        if member.bot:
            continue

        if get_member_team_rank(
            member
        ):

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
# TEAM EMBED
# ============================================================

def build_team_embed(
    guild: discord.Guild,
):

    members = get_all_team_members(
        guild
    )

    absent = sum(
        1
        for member in members
        if member_is_absent(member)
    )

    active = (
        len(members)
        - absent
    )

    embed = discord.Embed(
        title="👥 EHRP | SYSTEM • TEAMLISTE",
        description=(
            "## OFFIZIELLE TEAMÜBERSICHT\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** {len(members)}\n"
            f"🟢 **Aktiv:** {active}\n"
            f"🏖️ **Abgemeldet:** {absent}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Die Teamliste wird automatisch "
            "mit den Teamrollen synchronisiert."
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

                member_text = "\n".join(
                    member_lines
                )

            else:

                member_text = "—"

            lines.append(
                f"**{prefix} {role_name}**\n"
                f"{member_text}"
            )

        embed.add_field(
            name=section_name,
            value="\n\n".join(lines)[:1024],
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

                if TEAM_FOOTER_MARKER in footer:
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
                f"❌ Teamliste Update Fehler: {error}"
            )

    return changed


# ============================================================
# COG
# ============================================================

class Team(commands.Cog):

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
    # AUTO SYNC
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
                    f"❌ Team Auto-Sync Fehler: {error}"
                )


    @team_sync_loop.before_loop
    async def before_team_sync_loop(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # MEMBER UPDATE
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):

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
                f"❌ Member Update Fehler: {error}"
            )


    # ========================================================
    # /team_status
    # ========================================================

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

        members = get_all_team_members(
            interaction.guild
        )

        absent = sum(
            1
            for member in members
            if member_is_absent(member)
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
                        role_name
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
            text="EHRP | System • Team Management V4"
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
            "Zeigt die erkannten echten Discord-Teamrollen."
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

        detected_lines = []

        for role in reversed(
            interaction.guild.roles
        ):

            if role_is_ignored(
                role.name
            ):
                continue

            rank = match_known_rank(
                role.name
            )

            if rank is None:
                continue

            detected_lines.append(
                (
                    f"`{role.name}`\n"
                    f"↳ **{rank['prefix']} "
                    f"{rank['role_name']}**"
                )
            )

        embed = discord.Embed(
            title="🔎 EHRP | TEAM DEBUG",
            description=(
                "\n\n".join(
                    detected_lines
                )[:4000]
                if detected_lines
                else "❌ Keine Teamrollen erkannt."
            ),
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text="EHRP | System • Role Detection V4"
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
            if member_is_absent(member)
        )

        await interaction.followup.send(
            (
                "✅ **TEAM-SYNC ABGESCHLOSSEN**\n\n"
                f"👥 Teammitglieder: "
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
