from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks


# ============================================================
# EHRP | SYSTEM — TEAM SYSTEM
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

GERMAN_TIMEZONE = ZoneInfo("Europe/Berlin")


# ============================================================
# GALAXY ABMELDUNG
# ============================================================

GALAXY_ABMELDUNG_CHANNEL_ID = 1526950230346436690

ABGEMELDET_ROLE_ID = 1542855868650098718

ABGEMELDET_SUFFIX = " (Abgemeldet)"


# ============================================================
# TEAM RÄNGE
# HÖCHSTER RANG STEHT OBEN
# ============================================================

TEAM_RANKS = [

    # ========================================================
    # LEADEREBENE
    # ========================================================

    {
        "name": "Founder",
        "role_id": 1526952807838646334,
        "tag": "[FD]",
    },

    {
        "name": "Co. Founder",
        "role_id": 1526952825169510473,
        "tag": "[Co. FD]",
    },


    # ========================================================
    # KERNTEAM
    # ========================================================

    {
        "name": "Obervorstand",
        "role_id": 1526952877585596570,
        "tag": "[OVS]",
    },

    {
        "name": "Vorstand",
        "role_id": 1526952894891556864,
        "tag": "[VS]",
    },

    {
        "name": "Sachbearbeiter",
        "role_id": 1536099715412926584,
        "tag": "[SB]",
    },

    {
        "name": "Verwaltungsleitung",
        "role_id": 1526952911651995649,
        "tag": "[VL]",
    },

    {
        "name": "Hauptverwaltung",
        "role_id": 1526953865768075435,
        "tag": "[HV]",
    },


    # ========================================================
    # KERNTEAMVERWALTUNG
    # ========================================================

    {
        "name": "Archivleitung",
        "role_id": 1536100042354462802,
        "tag": "[AL]",
    },

    {
        "name": "Gesamtkoordinator",
        "role_id": 1532505961292501084,
        "tag": "[GT. K]",
    },

    {
        "name": "Teamkoordinator",
        "role_id": 1526955267416133653,
        "tag": "[TK]",
    },

    {
        "name": "Jr. Teamkoordinator",
        "role_id": 1526955292514980003,
        "tag": "[Jr. TK]",
    },

    {
        "name": "Head of Management",
        "role_id": 1532506490852737104,
        "tag": "[HoM]",
    },

    {
        "name": "Sr. Management",
        "role_id": 1532506146898706604,
        "tag": "[Sr. MA]",
    },

    {
        "name": "Manager",
        "role_id": 1526953952199839935,
        "tag": "[MA]",
    },

    {
        "name": "Stv. Manager",
        "role_id": 1526953970294063194,
        "tag": "[Stv. MA]",
    },


    # ========================================================
    # ADMINEBENE
    # ========================================================

    {
        "name": "Admin Koordinator",
        "role_id": 1532520713657909278,
        "tag": "[ADK]",
    },

    {
        "name": "Systemadmin",
        "role_id": 1526956576701677589,
        "tag": "[SAD]",
    },

    {
        "name": "Admin",
        "role_id": 1526956609048416429,
        "tag": "[AD]",
    },

    {
        "name": "Jr. Admin",
        "role_id": 1526956627704549408,
        "tag": "[Jr. AD]",
    },


    # ========================================================
    # MODERATOREBENE
    # ========================================================

    {
        "name": "Mod Koordinator",
        "role_id": 1526956664253579294,
        "tag": "[MOD. K]",
    },

    {
        "name": "Mod Spezialist",
        "role_id": 1526956700836429944,
        "tag": "[MOD. S]",
    },

    {
        "name": "Mod",
        "role_id": 1526956724089524386,
        "tag": "[MOD]",
    },

    {
        "name": "Jr. Mod",
        "role_id": 1532504668859662376,
        "tag": "[Jr. MOD]",
    },


    # ========================================================
    # SUPPORTEREBENE
    # ========================================================

    {
        "name": "Supporter Koordinator",
        "role_id": 1532504388503994568,
        "tag": "[SUP. K]",
    },

    {
        "name": "Supporter Spezialist",
        "role_id": 1526956760303140924,
        "tag": "[SUP. S]",
    },

    {
        "name": "Supporter",
        "role_id": 1526956795590086747,
        "tag": "[SUP]",
    },

    {
        "name": "Az. Supporter",
        "role_id": 1526956832822919331,
        "tag": "[Az. SUP]",
    },
]


TEAM_ROLE_IDS = {
    rank["role_id"]
    for rank in TEAM_RANKS
}


# ============================================================
# ALTE TAGS
# Damit alte Nicknames sauber ersetzt werden
# ============================================================

OLD_TEAM_TAGS = [

    "[T. K]",
    "[Jr. T. K]",
    "[AK]",
    "[A. K]",
    "[SYS. A]",

]


# ============================================================
# DEUTSCHE MONATE
# ============================================================

GERMAN_MONTHS = {

    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,

}


# ============================================================
# AKTIVE / GEPLANTE ABMELDUNGEN
# ============================================================

ABSENCES = {}


# ============================================================
# TEAM RANG FINDEN
# ============================================================

def get_team_rank(
    member: discord.Member,
):

    member_role_ids = {
        role.id
        for role in member.roles
    }

    for rank in TEAM_RANKS:

        if rank["role_id"] in member_role_ids:
            return rank

    return None


# ============================================================
# ABMELDUNG SUFFIX ENTFERNEN
# ============================================================

def remove_absence_suffix(
    nickname: str,
):

    cleaned = nickname.strip()

    cleaned = re.sub(
        r"\s*\(Abgemeldet\)$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*-\s*Abgemeldet$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip()


# ============================================================
# ALTE TEAM TAGS ENTFERNEN
# ============================================================

def remove_old_team_tag(
    nickname: str,
):

    cleaned = remove_absence_suffix(
        nickname
    )

    # Aktuelle Tags
    for rank in TEAM_RANKS:

        tag = re.escape(
            rank["tag"]
        )

        cleaned = re.sub(
            rf"^{tag}\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

    # Alte Tags
    for old_tag in OLD_TEAM_TAGS:

        escaped = re.escape(
            old_tag
        )

        cleaned = re.sub(
            rf"^{escaped}\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

    return cleaned


# ============================================================
# BASISNAME
# ============================================================

def get_base_name(
    member: discord.Member,
):

    current_name = (
        member.nick
        or member.global_name
        or member.name
    )

    return remove_old_team_tag(
        current_name
    )


# ============================================================
# ABGEMELDET ROLLE?
# ============================================================

def has_absence_role(
    member: discord.Member,
):

    return any(
        role.id == ABGEMELDET_ROLE_ID
        for role in member.roles
    )


# ============================================================
# NICKNAME BAUEN
# ============================================================

def build_team_nickname(
    member: discord.Member,
    rank,
):

    base_name = get_base_name(
        member
    )

    nickname = (
        f"{rank['tag']} {base_name}"
    )

    if has_absence_role(
        member
    ):
        nickname += ABGEMELDET_SUFFIX

    return nickname[:32]


# ============================================================
# EINZELNES MITGLIED SYNCHRONISIEREN
# ============================================================

async def sync_member(
    member: discord.Member,
):

    if member.bot:
        return False

    rank = get_team_rank(
        member
    )

    if rank is None:
        return False

    # Server Owner kann Discord nicht umbenennen
    if member.guild.owner_id == member.id:
        return False

    desired_nickname = build_team_nickname(
        member,
        rank,
    )

    current_nickname = (
        member.nick
        or member.global_name
        or member.name
    )

    if current_nickname == desired_nickname:
        return False

    try:

        await member.edit(
            nick=desired_nickname,
            reason=(
                "EHRP | System "
                "Team-Nickname-Synchronisierung"
            ),
        )

        return True

    except discord.Forbidden:

        print(
            f"❌ Keine Berechtigung für Nickname: {member}"
        )

    except discord.HTTPException as error:

        print(
            f"❌ Nickname Fehler bei {member}: {error}"
        )

    return False


# ============================================================
# SERVER SYNCHRONISIEREN
# ============================================================

async def sync_guild(
    guild: discord.Guild,
):

    changed = 0
    detected = 0

    for member in guild.members:

        rank = get_team_rank(
            member
        )

        if rank is None:
            continue

        detected += 1

        if await sync_member(
            member
        ):
            changed += 1

    return detected, changed


# ============================================================
# GALAXY DATUM PARSEN
# Beispiel:
# 28. August 2026 at 14:00
# 28. August 2026 um 14:00
# ============================================================

def parse_galaxy_datetime(
    value: str,
):

    if not value:
        return None

    cleaned = (
        value
        .replace("**", "")
        .replace("`", "")
        .strip()
    )

    pattern = (
        r"(\d{1,2})\.\s*"
        r"([A-Za-zÄÖÜäöüß]+)\s+"
        r"(\d{4})\s+"
        r"(?:at|um)\s+"
        r"(\d{1,2}):(\d{2})"
    )

    match = re.search(
        pattern,
        cleaned,
        re.IGNORECASE,
    )

    if not match:
        return None

    day = int(
        match.group(1)
    )

    month_name = (
        match.group(2)
        .lower()
        .strip()
    )

    year = int(
        match.group(3)
    )

    hour = int(
        match.group(4)
    )

    minute = int(
        match.group(5)
    )

    month = GERMAN_MONTHS.get(
        month_name
    )

    if month is None:
        return None

    try:

        return datetime(
            year,
            month,
            day,
            hour,
            minute,
            tzinfo=GERMAN_TIMEZONE,
        )

    except ValueError:

        return None


# ============================================================
# EMBED TEXT AUSLESEN
# ============================================================

def get_embed_text(
    embed: discord.Embed,
):

    parts = []

    if embed.title:
        parts.append(
            embed.title
        )

    if embed.description:
        parts.append(
            embed.description
        )

    for field in embed.fields:

        parts.append(
            field.name
        )

        parts.append(
            field.value
        )

    return "\n".join(
        parts
    )


# ============================================================
# USER AUS GALAXY NACHRICHT
# ============================================================

def extract_user_id(
    message: discord.Message,
):

    if message.mentions:
        return message.mentions[0].id

    for embed in message.embeds:

        text = get_embed_text(
            embed
        )

        match = re.search(
            r"<@!?(\d{15,25})>",
            text,
        )

        if match:

            return int(
                match.group(1)
            )

    return None


# ============================================================
# START + ENDE AUS GALAXY
# ============================================================

def extract_absence_times(
    message: discord.Message,
):

    all_text = []

    if message.content:
        all_text.append(
            message.content
        )

    for embed in message.embeds:

        all_text.append(
            get_embed_text(
                embed
            )
        )

    text = "\n".join(
        all_text
    )

    start_match = re.search(
        r"Vom\s*:?\s*"
        r"(\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s+\d{4}\s+"
        r"(?:at|um)\s+\d{1,2}:\d{2})",
        text,
        re.IGNORECASE,
    )

    end_match = re.search(
        r"Bis\s+zum\s*:?\s*"
        r"(\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s+\d{4}\s+"
        r"(?:at|um)\s+\d{1,2}:\d{2})",
        text,
        re.IGNORECASE,
    )

    if not start_match or not end_match:
        return None, None

    start = parse_galaxy_datetime(
        start_match.group(1)
    )

    end = parse_galaxy_datetime(
        end_match.group(1)
    )

    return start, end


# ============================================================
# IST GALAXY ABMELDUNG?
# ============================================================

def is_galaxy_absence_message(
    message: discord.Message,
):

    if (
        message.channel.id
        != GALAXY_ABMELDUNG_CHANNEL_ID
    ):
        return False

    if not message.author.bot:
        return False

    all_text = []

    if message.content:
        all_text.append(
            message.content
        )

    for embed in message.embeds:

        all_text.append(
            get_embed_text(
                embed
            )
        )

    text = "\n".join(
        all_text
    ).lower()

    return (
        "neue team abmeldung"
        in text
    )


# ============================================================
# GALAXY ABMELDUNG REGISTRIEREN
# ============================================================

async def register_absence_from_message(
    message: discord.Message,
):

    if not is_galaxy_absence_message(
        message
    ):
        return False

    user_id = extract_user_id(
        message
    )

    start, end = extract_absence_times(
        message
    )

    if user_id is None:

        print(
            "⚠️ Galaxy: User konnte nicht erkannt werden."
        )

        return False

    if start is None or end is None:

        print(
            "⚠️ Galaxy: Zeitraum konnte nicht erkannt werden."
        )

        return False

    if end <= start:

        print(
            "⚠️ Galaxy: Abmeldungsende liegt vor Start."
        )

        return False

    ABSENCES[user_id] = {
        "start": start,
        "end": end,
    }

    print(
        "🌙 Galaxy Abmeldung erkannt | "
        f"User {user_id} | "
        f"{start.strftime('%d.%m.%Y %H:%M')} → "
        f"{end.strftime('%d.%m.%Y %H:%M')}"
    )

    await process_single_absence(
        message.guild,
        user_id,
    )

    return True


# ============================================================
# ABMELDUNG VERARBEITEN
# ============================================================

async def process_single_absence(
    guild: discord.Guild,
    user_id: int,
):

    data = ABSENCES.get(
        user_id
    )

    if data is None:
        return

    member = guild.get_member(
        user_id
    )

    if member is None:
        return

    absence_role = guild.get_role(
        ABGEMELDET_ROLE_ID
    )

    if absence_role is None:

        print(
            "❌ Abgemeldet-Rolle wurde nicht gefunden."
        )

        return

    now = datetime.now(
        GERMAN_TIMEZONE
    )

    start = data["start"]
    end = data["end"]


    # ========================================================
    # ABMELDUNG NOCH NICHT GESTARTET
    # ========================================================

    if now < start:

        if absence_role in member.roles:

            try:

                await member.remove_roles(
                    absence_role,
                    reason=(
                        "EHRP | System "
                        "Abmeldung beginnt erst später"
                    ),
                )

            except discord.HTTPException:
                pass

        await sync_member(
            member
        )

        return


    # ========================================================
    # ABMELDUNG AKTIV
    # ========================================================

    if start <= now < end:

        if absence_role not in member.roles:

            try:

                await member.add_roles(
                    absence_role,
                    reason=(
                        "EHRP | System "
                        "Galaxy Team-Abmeldung"
                    ),
                )

                print(
                    f"🌙 Abgemeldet-Rolle vergeben: {member}"
                )

            except discord.Forbidden:

                print(
                    f"❌ Abgemeldet-Rolle kann bei {member} "
                    "nicht vergeben werden."
                )

                return

            except discord.HTTPException as error:

                print(
                    f"❌ Rollenfehler bei {member}: {error}"
                )

                return

        await sync_member(
            member
        )

        return


    # ========================================================
    # ABMELDUNG BEENDET
    # ========================================================

    if now >= end:

        if absence_role in member.roles:

            try:

                await member.remove_roles(
                    absence_role,
                    reason=(
                        "EHRP | System "
                        "Galaxy-Abmeldung abgelaufen"
                    ),
                )

                print(
                    f"✅ Abmeldung beendet: {member}"
                )

            except discord.Forbidden:

                print(
                    f"❌ Abgemeldet-Rolle kann bei {member} "
                    "nicht entfernt werden."
                )

                return

            except discord.HTTPException as error:

                print(
                    f"❌ Rollenfehler bei {member}: {error}"
                )

                return

        await sync_member(
            member
        )

        ABSENCES.pop(
            user_id,
            None,
        )


# ============================================================
# STATUS EMBED
# ============================================================

def build_status_embed(
    guild: discord.Guild,
):

    detected = []

    for member in guild.members:

        rank = get_team_rank(
            member
        )

        if rank:
            detected.append(
                member
            )

    now = datetime.now(
        GERMAN_TIMEZONE
    )

    active_absences = sum(
        1
        for data in ABSENCES.values()
        if data["start"] <= now < data["end"]
    )

    embed = discord.Embed(
        title="👥 EHRP | TEAM SYSTEM",
        description=(
            "## SYSTEM STATUS\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🟢 **Team-System:** ONLINE\n"
            "🟢 **Auto-Nicknames:** AKTIV\n"
            "🟢 **Galaxy-Abmeldungen:** AKTIV\n"
            "🟢 **Abgemeldet-Rolle:** AUTOMATISCH\n\n"
            f"👥 **Teammitglieder erkannt:** {len(detected)}\n"
            f"🌙 **Aktuell abgemeldet:** {active_absences}\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SUCCESS_COLOR,
    )

    embed.set_footer(
        text="EHRP | System • Team Management"
    )

    return embed


# ============================================================
# TEAM MAP
# ============================================================

def build_map_embed(
    guild: discord.Guild,
):

    lines = []

    for rank in TEAM_RANKS:

        role = guild.get_role(
            rank["role_id"]
        )

        if role:

            lines.append(
                f"✅ **{rank['name']}** → "
                f"`{rank['tag']}` → {role.mention}"
            )

        else:

            lines.append(
                f"❌ **{rank['name']}** → "
                f"`{rank['tag']}`"
            )

    embed = discord.Embed(
        title="🗺️ EHRP | TEAM MAP",
        description=(
            "## RANG → NAMETAG\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            + "\n".join(lines)
            + "\n\n━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_footer(
        text="EHRP | System • Team Rollen"
    )

    return embed


# ============================================================
# COG
# ============================================================

class TeamSystem(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot

        self.history_loaded = False

        self.auto_sync.start()

        self.absence_loop.start()


    def cog_unload(
        self,
    ):

        self.auto_sync.cancel()

        self.absence_loop.cancel()


    # ========================================================
    # GALAXY NACHRICHT DIREKT ERKENNEN
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):

        if message.guild is None:
            return

        if (
            message.channel.id
            != GALAXY_ABMELDUNG_CHANNEL_ID
        ):
            return

        await register_absence_from_message(
            message
        )


    # ========================================================
    # HISTORY BEI NEUSTART LADEN
    # ========================================================

    async def load_absences_from_history(
        self,
    ):

        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:

            channel = guild.get_channel(
                GALAXY_ABMELDUNG_CHANNEL_ID
            )

            if not isinstance(
                channel,
                discord.TextChannel,
            ):

                print(
                    "⚠️ Galaxy-Abmeldungs-Channel "
                    "wurde nicht gefunden."
                )

                continue

            try:

                async for message in channel.history(
                    limit=250,
                    oldest_first=False,
                ):

                    if not is_galaxy_absence_message(
                        message
                    ):
                        continue

                    user_id = extract_user_id(
                        message
                    )

                    start, end = extract_absence_times(
                        message
                    )

                    if (
                        user_id is None
                        or start is None
                        or end is None
                    ):
                        continue

                    now = datetime.now(
                        GERMAN_TIMEZONE
                    )

                    if end <= now:
                        continue

                    if user_id not in ABSENCES:

                        ABSENCES[user_id] = {
                            "start": start,
                            "end": end,
                        }

                print(
                    "✅ Galaxy-Abmeldungen geladen: "
                    f"{len(ABSENCES)}"
                )

            except discord.Forbidden:

                print(
                    "❌ Bot darf Galaxy-History nicht lesen."
                )

            except discord.HTTPException as error:

                print(
                    f"❌ Galaxy-History Fehler: {error}"
                )

        self.history_loaded = True


    # ========================================================
    # ABMELDUNG ALLE 30 SEKUNDEN PRÜFEN
    # ========================================================

    @tasks.loop(
        seconds=30
    )
    async def absence_loop(
        self,
    ):

        if not self.history_loaded:

            await self.load_absences_from_history()

        for guild in self.bot.guilds:

            for user_id in list(
                ABSENCES.keys()
            ):

                try:

                    await process_single_absence(
                        guild,
                        user_id,
                    )

                except Exception as error:

                    print(
                        "❌ Abmeldungsfehler | "
                        f"User {user_id}: {error}"
                    )


    @absence_loop.before_loop
    async def before_absence_loop(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # AUTOMATISCHER TEAM SYNC
    # ========================================================

    @tasks.loop(
        minutes=5
    )
    async def auto_sync(
        self,
    ):

        for guild in self.bot.guilds:

            try:

                detected, changed = await sync_guild(
                    guild
                )

                if changed:

                    print(
                        "👥 Team Sync | "
                        f"{guild.name} | "
                        f"{detected} erkannt | "
                        f"{changed} geändert"
                    )

            except Exception as error:

                print(
                    f"❌ Team Auto-Sync Fehler: {error}"
                )


    @auto_sync.before_loop
    async def before_auto_sync(
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

        before_roles = {
            role.id
            for role in before.roles
        }

        after_roles = {
            role.id
            for role in after.roles
        }

        if before_roles != after_roles:

            await sync_member(
                after
            )


    # ========================================================
    # /TEAM_STATUS
    # ========================================================

    @app_commands.command(
        name="team_status",
        description="Zeigt den Status des EHRP Team-Systems.",
    )
    async def team_status(
        self,
        interaction: discord.Interaction,
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Nur auf dem Server verfügbar.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            embed=build_status_embed(
                interaction.guild
            ),
            ephemeral=True,
        )


    # ========================================================
    # /TEAM_MAP
    # ========================================================

    @app_commands.command(
        name="team_map",
        description="Zeigt alle Team-Ränge und Nametags.",
    )
    async def team_map(
        self,
        interaction: discord.Interaction,
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Nur auf dem Server verfügbar.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            embed=build_map_embed(
                interaction.guild
            ),
            ephemeral=True,
        )


    # ========================================================
    # /TEAM_SYNC
    # ========================================================

    @app_commands.command(
        name="team_sync",
        description="Synchronisiert alle Team-Nicknames.",
    )
    async def team_sync(
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

        if not interaction.user.guild_permissions.manage_nicknames:

            await interaction.response.send_message(
                "❌ Du darfst keinen Team-Sync durchführen.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        detected, changed = await sync_guild(
            interaction.guild
        )

        embed = discord.Embed(
            title="✅ EHRP | TEAM SYNC",
            description=(
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥 **Teammitglieder erkannt:** {detected}\n"
                f"🔄 **Nicknames geändert:** {changed}\n\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=SUCCESS_COLOR,
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /TEAM_ABMELDUNG_SYNC
    # ========================================================

    @app_commands.command(
        name="team_abmeldung_sync",
        description="Liest Galaxy-Abmeldungen erneut ein.",
    )
    async def team_abmeldung_sync(
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

        if not interaction.user.guild_permissions.manage_roles:

            await interaction.response.send_message(
                "❌ Du darfst diesen Sync nicht durchführen.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        ABSENCES.clear()

        self.history_loaded = False

        await self.load_absences_from_history()

        for user_id in list(
            ABSENCES.keys()
        ):

            await process_single_absence(
                interaction.guild,
                user_id,
            )

        await interaction.followup.send(
            (
                "✅ **Galaxy-Abmeldungen synchronisiert.**\n\n"
                f"🌙 Laufende/geplante Abmeldungen: "
                f"**{len(ABSENCES)}**"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /TEAM_PANEL
    # ========================================================

    @app_commands.command(
        name="team_panel",
        description="Zeigt das Team-System Panel.",
    )
    async def team_panel(
        self,
        interaction: discord.Interaction,
    ):

        if interaction.guild is None:
            return

        embed = discord.Embed(
            title="👥 EHRP | TEAM MANAGEMENT",
            description=(
                "## TEAM SYSTEM\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "🏷️ **Automatische Nametags**\n"
                "Der höchste Team-Rang bestimmt das Kürzel.\n\n"
                "🌙 **Galaxy-Abmeldung**\n"
                "Galaxy-Abmeldungen werden automatisch erkannt.\n\n"
                "🎭 **Abgemeldet-Rolle**\n"
                "Während der Abmeldung wird automatisch die "
                "Abgemeldet-Rolle vergeben.\n\n"
                "✏️ **Nickname**\n"
                "Während der Abmeldung steht automatisch "
                "`(Abgemeldet)` hinter dem Namen.\n\n"
                "⏰ **Automatisches Ende**\n"
                "Nach Ablauf werden Rolle und "
                "`(Abgemeldet)` automatisch entfernt.\n\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=SYSTEM_COLOR,
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
        TeamSystem(bot)
    )
