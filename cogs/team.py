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
    {"name": "Founder", "role_id": 1526952807838646334, "tag": "[FD]"},
    {"name": "Co. Founder", "role_id": 1526952825169510473, "tag": "[Co. FD]"},

    {"name": "Obervorstand", "role_id": 1526952877585596570, "tag": "[OVS]"},
    {"name": "Vorstand", "role_id": 1526952894891556864, "tag": "[VS]"},
    {"name": "Sachbearbeiter", "role_id": 1536099715412926584, "tag": "[SB]"},
    {"name": "Verwaltungsleitung", "role_id": 1526952911651995649, "tag": "[VL]"},
    {"name": "Hauptverwaltung", "role_id": 1526953865768075435, "tag": "[HV]"},

    {"name": "Archivleitung", "role_id": 1536100042354462802, "tag": "[AL]"},
    {"name": "Gesamtkoordinator", "role_id": 1532505961292501084, "tag": "[GT. K]"},
    {"name": "Teamkoordinator", "role_id": 1526955267416133653, "tag": "[TK]"},
    {"name": "Jr. Teamkoordinator", "role_id": 1526955292514980003, "tag": "[Jr. TK]"},

    {"name": "Head of Management", "role_id": 1532506490852737104, "tag": "[HoM]"},
    {"name": "Sr. Management", "role_id": 1532506146898706604, "tag": "[Sr. MA]"},
    {"name": "Manager", "role_id": 1526953952199839935, "tag": "[MA]"},
    {"name": "Stv. Manager", "role_id": 1526953970294063194, "tag": "[Stv. MA]"},

    {"name": "Admin Koordinator", "role_id": 1532520713657909278, "tag": "[ADK]"},
    {"name": "Systemadmin", "role_id": 1526956576701677589, "tag": "[SAD]"},
    {"name": "Admin", "role_id": 1526956609048416429, "tag": "[AD]"},
    {"name": "Jr. Admin", "role_id": 1526956627704549408, "tag": "[Jr. AD]"},

    {"name": "Mod Koordinator", "role_id": 1526956664253579294, "tag": "[MOD. K]"},
    {"name": "Mod Spezialist", "role_id": 1526956700836429944, "tag": "[MOD. S]"},
    {"name": "Mod", "role_id": 1526956724089524386, "tag": "[MOD]"},
    {"name": "Jr. Mod", "role_id": 1532504668859662376, "tag": "[Jr. MOD]"},

    {"name": "Supporter Koordinator", "role_id": 1532504388503994568, "tag": "[SUP. K]"},
    {"name": "Supporter Spezialist", "role_id": 1526956760303140924, "tag": "[SUP. S]"},
    {"name": "Supporter", "role_id": 1526956795590086747, "tag": "[SUP]"},
    {"name": "Az. Supporter", "role_id": 1526956832822919331, "tag": "[Az. SUP]"},
]


# ============================================================
# ALTE TAGS
# ============================================================

OLD_TEAM_TAGS = [
    "[T. K]",
    "[Jr. T. K]",
    "[AK]",
    "[A. K]",
    "[SYS. A]",
]


# ============================================================
# GALAXY DATUM
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


ABSENCES = {}


# ============================================================
# TEAM RANG
# ============================================================

def get_team_rank(member: discord.Member):
    role_ids = {role.id for role in member.roles}

    for rank in TEAM_RANKS:
        if rank["role_id"] in role_ids:
            return rank

    return None


# ============================================================
# NAMETAG BEREINIGEN
# ============================================================

def remove_absence_suffix(name: str):
    name = re.sub(
        r"\s*\(Abgemeldet\)$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    name = re.sub(
        r"\s*-\s*Abgemeldet$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    return name.strip()


def remove_team_tag(name: str):
    cleaned = remove_absence_suffix(name)

    all_tags = [rank["tag"] for rank in TEAM_RANKS] + OLD_TEAM_TAGS

    for tag in all_tags:
        cleaned = re.sub(
            rf"^{re.escape(tag)}\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

    return cleaned


def get_base_name(member: discord.Member):
    current = member.nick or member.global_name or member.name

    return remove_team_tag(current)


# ============================================================
# ABMELDUNG
# ============================================================

def has_absence_role(member: discord.Member):
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
    base_name = get_base_name(member)

    nickname = f"{rank['tag']} {base_name}"

    if has_absence_role(member):
        nickname += ABGEMELDET_SUFFIX

    return nickname[:32]


# ============================================================
# KANN BOT MEMBER ÄNDERN?
# ============================================================

def bot_can_edit_member(
    guild: discord.Guild,
    member: discord.Member,
):
    me = guild.me

    if me is None:
        return False

    if guild.owner_id == member.id:
        return False

    if not me.guild_permissions.manage_nicknames:
        return False

    if member.top_role >= me.top_role:
        return False

    return True


# ============================================================
# MEMBER SYNC
# ============================================================

async def sync_member(
    member: discord.Member,
):
    if member.bot:
        return False

    rank = get_team_rank(member)

    if rank is None:
        return False

    desired = build_team_nickname(
        member,
        rank,
    )

    current = member.nick or member.global_name or member.name

    if current == desired:
        return False

    if not bot_can_edit_member(
        member.guild,
        member,
    ):
        print(
            f"⚠️ Nickname nicht änderbar: {member} | "
            f"Member-Rolle: {member.top_role.name} | "
            f"Bot-Rolle: {member.guild.me.top_role.name if member.guild.me else 'unbekannt'}"
        )
        return False

    try:
        await member.edit(
            nick=desired,
            reason="EHRP | System Team-Nickname Sync",
        )

        print(
            f"✅ Nickname geändert: {member} -> {desired}"
        )

        return True

    except discord.Forbidden:
        print(
            f"❌ Discord blockiert Nickname-Änderung bei {member}"
        )

    except discord.HTTPException as error:
        print(
            f"❌ Nickname Fehler bei {member}: {error}"
        )

    return False


# ============================================================
# SERVER SYNC
# ============================================================

async def sync_guild(
    guild: discord.Guild,
):
    detected = 0
    changed = 0

    for member in guild.members:
        if get_team_rank(member) is None:
            continue

        detected += 1

        if await sync_member(member):
            changed += 1

    return detected, changed


# ============================================================
# GALAXY EMBED TEXT
# ============================================================

def get_embed_text(
    embed: discord.Embed,
):
    parts = []

    if embed.title:
        parts.append(embed.title)

    if embed.description:
        parts.append(embed.description)

    for field in embed.fields:
        parts.append(field.name)
        parts.append(field.value)

    return "\n".join(parts)


# ============================================================
# GALAXY USER ID
# ============================================================

def extract_user_id(
    message: discord.Message,
):
    if message.mentions:
        return message.mentions[0].id

    for embed in message.embeds:
        text = get_embed_text(embed)

        match = re.search(
            r"<@!?(\d{15,25})>",
            text,
        )

        if match:
            return int(match.group(1))

    return None


# ============================================================
# GALAXY DATUM PARSEN
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

    day = int(match.group(1))
    month_name = match.group(2).lower()
    year = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))

    month = GERMAN_MONTHS.get(month_name)

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
# GALAXY ABMELDUNGSZEITEN
# ============================================================

def extract_absence_times(
    message: discord.Message,
):
    parts = []

    if message.content:
        parts.append(message.content)

    for embed in message.embeds:
        parts.append(
            get_embed_text(embed)
        )

    text = "\n".join(parts)

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

    return (
        parse_galaxy_datetime(start_match.group(1)),
        parse_galaxy_datetime(end_match.group(1)),
    )


# ============================================================
# GALAXY NACHRICHT ERKENNEN
# ============================================================

def is_galaxy_absence_message(
    message: discord.Message,
):
    if message.channel.id != GALAXY_ABMELDUNG_CHANNEL_ID:
        return False

    if not message.author.bot:
        return False

    parts = [message.content or ""]

    for embed in message.embeds:
        parts.append(
            get_embed_text(embed)
        )

    text = "\n".join(parts).lower()

    return "neue team abmeldung" in text


# ============================================================
# ABMELDUNG REGISTRIEREN
# ============================================================

async def register_absence_from_message(
    message: discord.Message,
):
    if not is_galaxy_absence_message(message):
        return

    user_id = extract_user_id(message)
    start, end = extract_absence_times(message)

    if user_id is None or start is None or end is None:
        print(
            "⚠️ Galaxy-Abmeldung konnte nicht vollständig gelesen werden."
        )
        return

    ABSENCES[user_id] = {
        "start": start,
        "end": end,
    }

    await process_single_absence(
        message.guild,
        user_id,
    )


# ============================================================
# ABMELDUNG VERARBEITEN
# ============================================================

async def process_single_absence(
    guild: discord.Guild,
    user_id: int,
):
    data = ABSENCES.get(user_id)

    if not data:
        return

    member = guild.get_member(user_id)

    if member is None:
        return

    absence_role = guild.get_role(
        ABGEMELDET_ROLE_ID
    )

    if absence_role is None:
        print(
            "❌ Abgemeldet-Rolle nicht gefunden."
        )
        return

    now = datetime.now(
        GERMAN_TIMEZONE
    )

    start = data["start"]
    end = data["end"]

    if now < start:
        return

    if start <= now < end:
        if absence_role not in member.roles:
            try:
                await member.add_roles(
                    absence_role,
                    reason="EHRP | Galaxy Abmeldung",
                )

            except discord.Forbidden:
                print(
                    f"❌ Abgemeldet-Rolle kann bei {member} nicht vergeben werden."
                )
                return

        await sync_member(member)

        return

    if now >= end:
        if absence_role in member.roles:
            try:
                await member.remove_roles(
                    absence_role,
                    reason="EHRP | Galaxy Abmeldung beendet",
                )

            except discord.Forbidden:
                print(
                    f"❌ Abgemeldet-Rolle kann bei {member} nicht entfernt werden."
                )
                return

        await sync_member(member)

        ABSENCES.pop(
            user_id,
            None,
        )


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


    def cog_unload(self):
        self.auto_sync.cancel()
        self.absence_loop.cancel()


    # ========================================================
    # GALAXY LIVE
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):
        if message.guild is None:
            return

        await register_absence_from_message(
            message
        )


    # ========================================================
    # ROLLENÄNDERUNG
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
            await sync_member(after)


    # ========================================================
    # AUTO TEAM SYNC
    # ========================================================

    @tasks.loop(
        minutes=5
    )
    async def auto_sync(self):
        for guild in self.bot.guilds:
            await sync_guild(guild)


    @auto_sync.before_loop
    async def before_auto_sync(self):
        await self.bot.wait_until_ready()


    # ========================================================
    # ABMELDUNGS LOOP
    # ========================================================

    @tasks.loop(
        seconds=30
    )
    async def absence_loop(self):
        for guild in self.bot.guilds:
            for user_id in list(
                ABSENCES.keys()
            ):
                await process_single_absence(
                    guild,
                    user_id,
                )


    @absence_loop.before_loop
    async def before_absence_loop(self):
        await self.bot.wait_until_ready()


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
        if interaction.guild is None:
            return

        await interaction.response.defer(
            ephemeral=True
        )

        detected, changed = await sync_guild(
            interaction.guild
        )

        await interaction.followup.send(
            (
                "✅ **Team-Sync abgeschlossen.**\n\n"
                f"👥 Erkannte Teammitglieder: **{detected}**\n"
                f"🔄 Geänderte Nicknames: **{changed}**"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /TEAM_NICK_DEBUG
    # ========================================================

    @app_commands.command(
        name="team_nick_debug",
        description="Prüft, warum dein Nickname eventuell nicht geändert wird.",
    )
    async def team_nick_debug(
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

        member = interaction.user
        bot_member = interaction.guild.me

        rank = get_team_rank(member)

        if rank is None:
            text = (
                "❌ Keine deiner Rollen ist im Team-System hinterlegt."
            )

        elif bot_member is None:
            text = (
                "❌ Bot-Mitglied konnte nicht erkannt werden."
            )

        else:
            text = (
                f"🏷️ **Erkannter Rang:** {rank['name']}\n"
                f"🔖 **Tag:** `{rank['tag']}`\n"
                f"👤 **Deine höchste Rolle:** {member.top_role.mention}\n"
                f"🤖 **Höchste Bot-Rolle:** {bot_member.top_role.mention}\n"
                f"✏️ **Nicknames verwalten:** "
                f"{'✅' if bot_member.guild_permissions.manage_nicknames else '❌'}\n"
                f"📊 **Bot über dir:** "
                f"{'✅' if bot_member.top_role > member.top_role else '❌'}\n\n"
                f"🎯 Gewünschter Nickname:\n"
                f"`{build_team_nickname(member, rank)}`"
            )

        await interaction.response.send_message(
            text,
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
