from __future__ import annotations

import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — GALAXY TEAM SYNC
# ============================================================

GALAXY_TEAM_CHANNEL_ID = 1526942701092606062

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C

TEAM_PANEL_MARKER = "EHRP_GALAXY_TEAM_SYNC_V1"


# ============================================================
# GALAXY RANG -> NAMETAG
#
# Diese Zuordnung kommt direkt aus deiner Galaxy-Team-Liste.
# ============================================================

GALAXY_RANKS = [
    {
        "name": "Founder",
        "tag": "[FD]",
        "section": "👑 Leitung",
    },
    {
        "name": "Co-Founder",
        "tag": "[Co. FD]",
        "section": "👑 Leitung",
    },
    {
        "name": "Obervorstand",
        "tag": "[OVS]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Vorstand",
        "tag": "[VS]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Sachbearbeiter",
        "tag": "[SB]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Verwaltungsleitung",
        "tag": "[VL]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Hauptverwaltung",
        "tag": "[HV]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Archivleitung",
        "tag": "[AL]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Gesamtkoordinator",
        "tag": "[GT. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Teamkoordinator",
        "tag": "[T. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Jr. Teamkoordinator",
        "tag": "[Jr. T. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Head of Management",
        "tag": "[HoM]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Sr. Management",
        "tag": "[Sr. M]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Manager",
        "tag": "[M]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Stv. Manager",
        "tag": "[Stv. M]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Admin-Koordinator",
        "tag": "[A. K]",
        "section": "⚙️ Management",
    },
    {
        "name": "Systemadministrator",
        "tag": "[SYS. A]",
        "section": "⚙️ Management",
    },
    {
        "name": "Administrator",
        "tag": "[AD]",
        "section": "⚙️ Management",
    },
    {
        "name": "Jr. Administrator",
        "tag": "[Jr. AD]",
        "section": "⚙️ Management",
    },
    {
        "name": "Mod-Koordinator",
        "tag": "[MOD. K]",
        "section": "🔨 Administration",
    },
    {
        "name": "Moderations-Spezialist",
        "tag": "[MOD. S]",
        "section": "🔨 Administration",
    },
    {
        "name": "Moderator",
        "tag": "[MOD]",
        "section": "🔨 Administration",
    },
    {
        "name": "Jr. Moderator",
        "tag": "[Jr. MOD]",
        "section": "🔨 Administration",
    },
    {
        "name": "Sup-Koordinator",
        "tag": "[SUP. K]",
        "section": "🎧 Moderatoren",
    },
    {
        "name": "Support-Spezialist",
        "tag": "[SUP. S]",
        "section": "🎧 Moderatoren",
    },
    {
        "name": "Supporter",
        "tag": "[SUP]",
        "section": "🎧 Moderatoren",
    },
    {
        "name": "Az. Supporter",
        "tag": "[SUP]",
        "section": "🎧 Moderatoren",
    },
]


# ============================================================
# ABMELDUNG
# ============================================================

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
# TEXT NORMALISIEREN
# ============================================================

def normalize_text(
    text: str,
) -> str:

    text = text.casefold()

    text = (
        text.replace("»", " ")
        .replace("@", " ")
        .replace("•", " ")
        .replace("|", " ")
        .replace("—", " ")
        .replace("–", " ")
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# GALAXY RANG FINDEN
# ============================================================

def find_rank_by_heading(
    heading: str,
):

    normalized_heading = normalize_text(
        heading
    )

    # längere Namen zuerst
    sorted_ranks = sorted(
        GALAXY_RANKS,
        key=lambda rank: len(rank["name"]),
        reverse=True,
    )

    for rank in sorted_ranks:

        rank_name = normalize_text(
            rank["name"]
        )

        if rank_name in normalized_heading:
            return rank

    return None


# ============================================================
# EMBEDS AUS GALAXY LESEN
# ============================================================

async def get_latest_galaxy_team_messages(
    guild: discord.Guild,
):
    channel = guild.get_channel(
        GALAXY_TEAM_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        print(
            "❌ Galaxy Team-Channel nicht gefunden."
        )
        return []

    messages = []

    try:
        async for message in channel.history(
            limit=30,
            oldest_first=False,
        ):

            if not message.author.bot:
                continue

            # Galaxy-Teamliste erkennen
            has_team_embed = False

            for embed in message.embeds:

                title = (
                    embed.title
                    or ""
                )

                description = (
                    embed.description
                    or ""
                )

                combined = (
                    title
                    + " "
                    + description
                ).casefold()

                if (
                    "teamliste" in combined
                    or "team-liste" in combined
                    or "staff" in combined
                ):
                    has_team_embed = True
                    break

                # Auch reine Rang-Embeds berücksichtigen
                for rank in GALAXY_RANKS:

                    if normalize_text(
                        rank["name"]
                    ) in normalize_text(
                        combined
                    ):
                        has_team_embed = True
                        break

                if has_team_embed:
                    break

            if has_team_embed:
                messages.append(
                    message
                )

        return list(
            reversed(messages)
        )

    except (
        discord.Forbidden,
        discord.HTTPException,
    ) as error:

        print(
            f"❌ Galaxy-Liste konnte nicht gelesen werden: {error}"
        )

        return []


# ============================================================
# USER AUS EMBEDS EXTRAHIEREN
# ============================================================

def extract_user_ids(
    text: str,
) -> list[int]:

    if not text:
        return []

    ids = re.findall(
        r"<@!?(\d+)>",
        text,
    )

    return [
        int(user_id)
        for user_id in ids
    ]


# ============================================================
# GALAXY TEAMSTRUKTUR PARSEN
# ============================================================

async def parse_galaxy_team(
    guild: discord.Guild,
):
    messages = await get_latest_galaxy_team_messages(
        guild
    )

    result = {}

    for rank in GALAXY_RANKS:
        result[
            rank["name"]
        ] = []

    current_rank = None

    for message in messages:

        for embed in message.embeds:

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            if embed.title:

                detected = find_rank_by_heading(
                    embed.title
                )

                if detected:
                    current_rank = detected

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            if embed.description:

                lines = embed.description.splitlines()

                for line in lines:

                    detected = find_rank_by_heading(
                        line
                    )

                    if detected:
                        current_rank = detected

                    user_ids = extract_user_ids(
                        line
                    )

                    if (
                        current_rank
                        and user_ids
                    ):

                        for user_id in user_ids:

                            if (
                                user_id
                                not in result[
                                    current_rank["name"]
                                ]
                            ):
                                result[
                                    current_rank["name"]
                                ].append(
                                    user_id
                                )

            # ------------------------------------------------
            # FIELDS
            # ------------------------------------------------

            for field in embed.fields:

                detected = find_rank_by_heading(
                    field.name
                )

                if detected:
                    current_rank = detected

                user_ids = extract_user_ids(
                    field.value
                )

                if (
                    current_rank
                    and user_ids
                ):

                    for user_id in user_ids:

                        if (
                            user_id
                            not in result[
                                current_rank["name"]
                            ]
                        ):
                            result[
                                current_rank["name"]
                            ].append(
                                user_id
                            )

    return result


# ============================================================
# USER -> GALAXY RANG
# ============================================================

async def get_member_galaxy_rank(
    member: discord.Member,
):
    parsed = await parse_galaxy_team(
        member.guild
    )

    for rank in GALAXY_RANKS:

        member_ids = parsed.get(
            rank["name"],
            []
        )

        if member.id in member_ids:
            return rank

    return None


# ============================================================
# ABGEMELDET?
# ============================================================

def member_is_absent(
    member: discord.Member,
) -> bool:

    for role in member.roles:

        role_name = role.name.casefold()

        for keyword in ABSENCE_KEYWORDS:

            if keyword in role_name:
                return True

    return False


# ============================================================
# ALTEN TEAMTAG ENTFERNEN
# ============================================================

ALL_TAGS = sorted(
    {
        rank["tag"]
        for rank in GALAXY_RANKS
    },
    key=len,
    reverse=True,
)


def clean_member_name(
    member: discord.Member,
) -> str:

    name = (
        member.nick
        or member.global_name
        or member.name
    )

    name = re.sub(
        r"\s*-\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

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
# NAMETAG SYNC
# ============================================================

async def sync_member_from_galaxy(
    member: discord.Member,
    parsed_team: dict,
) -> bool:

    if member.bot:
        return False

    guild = member.guild
    bot_member = guild.me

    if bot_member is None:
        return False

    if member.id == guild.owner_id:
        return False

    if (
        member.top_role
        >= bot_member.top_role
    ):
        return False

    found_rank = None

    for rank in GALAXY_RANKS:

        if member.id in parsed_team.get(
            rank["name"],
            []
        ):
            found_rank = rank
            break

    # --------------------------------------------------------
    # NICHT MEHR IN GALAXY-LISTE
    # --------------------------------------------------------

    if found_rank is None:

        if member.nick is None:
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
                    "nicht mehr in Galaxy-Team-Liste"
                ),
            )

            return True

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            return False

    # --------------------------------------------------------
    # IN GALAXY-LISTE
    # --------------------------------------------------------

    base_name = clean_member_name(
        member
    )

    nickname = (
        f"{found_rank['tag']} "
        f"{base_name}"
    )

    if member_is_absent(
        member
    ):
        nickname += " - Abgemeldet"

    nickname = nickname[:32]

    if member.nick == nickname:
        return False

    try:
        await member.edit(
            nick=nickname,
            reason=(
                "EHRP | System "
                f"Galaxy Sync -> {found_rank['name']}"
            ),
        )

        print(
            f"✅ Galaxy Sync: "
            f"{member.name} -> {nickname}"
        )

        return True

    except discord.Forbidden:

        print(
            f"⚠️ Nickname nicht änderbar: {member}"
        )

    except discord.HTTPException as error:

        print(
            f"❌ Nickname Fehler {member}: {error}"
        )

    return False


# ============================================================
# ALLE GALAXY TEAMMITGLIEDER
# ============================================================

def get_team_member_ids(
    parsed_team: dict,
) -> set[int]:

    result = set()

    for ids in parsed_team.values():

        result.update(
            ids
        )

    return result


# ============================================================
# UNSERE TEAMLISTE BAUEN
# ============================================================

async def build_team_embed(
    guild: discord.Guild,
):
    parsed = await parse_galaxy_team(
        guild
    )

    team_ids = get_team_member_ids(
        parsed
    )

    members = []

    for user_id in team_ids:

        member = guild.get_member(
            user_id
        )

        if member:
            members.append(
                member
            )

    absent = sum(
        1
        for member in members
        if member_is_absent(member)
    )

    embed = discord.Embed(
        title="👥 EHRP | SYSTEM • TEAMLISTE",
        description=(
            "## GALAXY SYNCHRONISIERTE TEAMLISTE\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** {len(members)}\n"
            f"🟢 **Aktiv:** {len(members) - absent}\n"
            f"🏖️ **Abgemeldet:** {absent}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Quelle: **EHRP | Galaxybot**\n"
            "Nametags werden automatisch "
            "aus der Galaxy-Team-Liste übernommen."
        ),
        color=SYSTEM_COLOR,
    )

    sections = []

    for rank in GALAXY_RANKS:

        if rank["section"] not in sections:
            sections.append(
                rank["section"]
            )

    for section in sections:

        lines = []

        for rank in GALAXY_RANKS:

            if rank["section"] != section:
                continue

            ids = parsed.get(
                rank["name"],
                []
            )

            users = []

            for user_id in ids:

                member = guild.get_member(
                    user_id
                )

                if member:

                    status = (
                        "🏖️"
                        if member_is_absent(member)
                        else "🟢"
                    )

                    users.append(
                        f"{status} {member.mention}"
                    )

            if users:

                user_text = "\n".join(
                    users
                )

            else:

                user_text = "—"

            lines.append(
                f"**{rank['tag']} {rank['name']}**\n"
                f"{user_text}"
            )

        embed.add_field(
            name=section,
            value="\n\n".join(lines)[:1024],
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{TEAM_PANEL_MARKER} • "
            "Galaxy Auto-Sync"
        )
    )

    return embed


# ============================================================
# PANEL FINDEN
# ============================================================

async def find_system_team_panel(
    guild: discord.Guild,
):

    if guild.me is None:
        return None

    for channel in guild.text_channels:

        perms = channel.permissions_for(
            guild.me
        )

        if not (
            perms.view_channel
            and perms.read_message_history
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

                if TEAM_PANEL_MARKER in footer:
                    return message

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            continue

    return None


# ============================================================
# FULL GALAXY SYNC
# ============================================================

async def full_galaxy_sync(
    guild: discord.Guild,
):

    parsed = await parse_galaxy_team(
        guild
    )

    changed = 0

    for member in guild.members:

        if member.bot:
            continue

        if await sync_member_from_galaxy(
            member,
            parsed,
        ):
            changed += 1

    panel = await find_system_team_panel(
        guild
    )

    if panel:

        try:

            await panel.edit(
                embed=await build_team_embed(
                    guild
                )
            )

        except discord.HTTPException:
            pass

    return changed, parsed


# ============================================================
# COG
# ============================================================

class Team(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot
        self.galaxy_sync_loop.start()


    def cog_unload(
        self,
    ):

        self.galaxy_sync_loop.cancel()


    # ========================================================
    # AUTO-SYNC
    # ========================================================

    @tasks.loop(
        minutes=5
    )
    async def galaxy_sync_loop(
        self,
    ):

        for guild in self.bot.guilds:

            try:

                await full_galaxy_sync(
                    guild
                )

            except Exception as error:

                print(
                    f"❌ Galaxy Team Sync Fehler: {error}"
                )


    @galaxy_sync_loop.before_loop
    async def before_galaxy_sync(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # /team_galaxy
    # ========================================================

    @app_commands.command(
        name="team_galaxy",
        description=(
            "Zeigt, welche Mitglieder "
            "aus Galaxy erkannt wurden."
        ),
    )
    async def team_galaxy(
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

        parsed = await parse_galaxy_team(
            interaction.guild
        )

        lines = []

        for rank in GALAXY_RANKS:

            ids = parsed.get(
                rank["name"],
                []
            )

            if not ids:
                continue

            names = []

            for user_id in ids:

                member = interaction.guild.get_member(
                    user_id
                )

                if member:
                    names.append(
                        member.mention
                    )
                else:
                    names.append(
                        f"`{user_id}`"
                    )

            lines.append(
                (
                    f"**{rank['tag']} "
                    f"{rank['name']}**\n"
                    + "\n".join(names)
                )
            )

        embed = discord.Embed(
            title="🪐 EHRP | GALAXY TEAM IMPORT",
            description=(
                "\n\n".join(lines)[:4000]
                if lines
                else (
                    "❌ Keine Galaxy-Teammitglieder "
                    "wurden erkannt."
                )
            ),
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text=(
                "Quelle: Galaxy-Team-Liste • "
                "keine Serverrollen-Auswertung"
            )
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_sync
    # ========================================================

    @app_commands.command(
        name="team_sync",
        description=(
            "Synchronisiert Nametags "
            "mit der Galaxy-Team-Liste."
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

        changed, parsed = await full_galaxy_sync(
            interaction.guild
        )

        team_ids = get_team_member_ids(
            parsed
        )

        await interaction.followup.send(
            (
                "✅ **GALAXY TEAM-SYNC FERTIG**\n\n"
                f"👥 Galaxy-Teammitglieder: "
                f"**{len(team_ids)}**\n"
                f"✏️ Nametags geändert: "
                f"**{changed}**\n\n"
                "Quelle: EHRP | Galaxybot"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /team_status
    # ========================================================

    @app_commands.command(
        name="team_status",
        description=(
            "Zeigt den Status des "
            "Galaxy-Team-Syncs."
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

        await interaction.response.defer(
            ephemeral=True
        )

        parsed = await parse_galaxy_team(
            interaction.guild
        )

        team_ids = get_team_member_ids(
            parsed
        )

        active_ranks = sum(
            1
            for ids in parsed.values()
            if ids
        )

        embed = discord.Embed(
            title="⚙️ EHRP | SYSTEM • TEAM STATUS",
            description=(
                "## GALAXY SYNC\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🟢 **System:** Online\n"
                "🪐 **Quelle:** Galaxybot\n"
                f"👥 **Teammitglieder erkannt:** "
                f"{len(team_ids)}\n"
                f"🏷️ **Aktive Galaxy-Ränge:** "
                f"{active_ranks}\n"
                "🔄 **Auto-Sync:** AKTIV\n"
                "⏱️ **Intervall:** 5 Minuten\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ Serverrollen werden nicht mehr "
                "zur Rangbestimmung benutzt."
            ),
            color=SUCCESS_COLOR,
        )

        embed.set_footer(
            text="EHRP | System • Galaxy Team Sync"
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /team_panel
    # ========================================================

    @app_commands.command(
        name="team_panel",
        description=(
            "Erstellt die eigene "
            "Galaxy-synchronisierte Teamliste."
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

        old_panel = await find_system_team_panel(
            interaction.guild
        )

        embed = await build_team_embed(
            interaction.guild
        )

        if (
            old_panel
            and old_panel.channel.id
            == interaction.channel.id
        ):

            await old_panel.edit(
                embed=embed
            )

            await interaction.followup.send(
                "✅ Teamliste aktualisiert.",
                ephemeral=True,
            )

            return

        new_message = await interaction.channel.send(
            embed=embed
        )

        if old_panel:

            try:
                await old_panel.delete()

            except discord.HTTPException:
                pass

        await interaction.followup.send(
            (
                "✅ **Galaxy-Team-Panel erstellt**\n"
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
