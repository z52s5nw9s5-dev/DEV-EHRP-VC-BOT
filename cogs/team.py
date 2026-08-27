from __future__ import annotations

import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — TEAM MANAGEMENT
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C

TEAM_PANEL_MARKER = "EHRP_TEAM_SYSTEM_FINAL_V1"


# ============================================================
# FESTE TEAMROLLEN
# Reihenfolge = Rangfolge
# Höchster Rang gewinnt
# ============================================================

TEAM_RANKS = [
    {
        "name": "Founder",
        "role_id": 1526952807838646334,
        "tag": "[FD]",
        "section": "👑 Leitung",
    },
    {
        "name": "Co-Founder",
        "role_id": 1526952825169510473,
        "tag": "[Co. FD]",
        "section": "👑 Leitung",
    },
    {
        "name": "Obervorstand",
        "role_id": 1526952877585596570,
        "tag": "[OVS]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Vorstand",
        "role_id": 1526952894891556864,
        "tag": "[VS]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Sachbearbeiter",
        "role_id": 1536099715412926584,
        "tag": "[SB]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Verwaltungsleitung",
        "role_id": 1526952911651995649,
        "tag": "[VL]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Hauptverwaltung",
        "role_id": 1526953865768075435,
        "tag": "[HV]",
        "section": "⚜️ Leaderebene",
    },
    {
        "name": "Archivleitung",
        "role_id": 1536100042354462802,
        "tag": "[AL]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Gesamtkoordinator",
        "role_id": 1532505961292501084,
        "tag": "[GT. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Teamkoordinator",
        "role_id": 1526955267416133653,
        "tag": "[T. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Jr. Teamkoordinator",
        "role_id": 1526955292514980003,
        "tag": "[Jr. T. K]",
        "section": "💎 Kernteam",
    },
    {
        "name": "Head of Management",
        "role_id": 1532506490852737104,
        "tag": "[HoM]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Sr. Management",
        "role_id": 1532506146898706604,
        "tag": "[Sr. MA]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Manager",
        "role_id": 1526953952199839935,
        "tag": "[MA]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Stv. Manager",
        "role_id": 1526953970294063194,
        "tag": "[Stv. MA]",
        "section": "🛡️ Teamverwaltung",
    },
    {
        "name": "Admin-Koordinator",
        "role_id": 1532520713657909278,
        "tag": "[A. K]",
        "section": "⚙️ Management",
    },
    {
        "name": "Systemadministrator",
        "role_id": 1526956576701677589,
        "tag": "[SYS. A]",
        "section": "⚙️ Management",
    },
    {
        "name": "Administrator",
        "role_id": 1526956609048416429,
        "tag": "[AD]",
        "section": "⚙️ Management",
    },
    {
        "name": "Jr. Administrator",
        "role_id": 1526956627704549408,
        "tag": "[Jr. AD]",
        "section": "⚙️ Management",
    },
    {
        "name": "Mod-Koordinator",
        "role_id": 1526956664253579294,
        "tag": "[MOD. K]",
        "section": "🔨 Administration",
    },
    {
        "name": "Moderations-Spezialist",
        "role_id": 1526956700836429944,
        "tag": "[MOD. S]",
        "section": "🔨 Administration",
    },
    {
        "name": "Moderator",
        "role_id": 1526956724089524386,
        "tag": "[MOD]",
        "section": "🔨 Administration",
    },
    {
        "name": "Jr. Moderator",
        "role_id": 1532504668859662376,
        "tag": "[Jr. MOD]",
        "section": "🔨 Administration",
    },
    {
        "name": "Sup-Koordinator",
        "role_id": 1532504388503994568,
        "tag": "[SUP. K]",
        "section": "🎧 Moderation & Support",
    },
    {
        "name": "Support-Spezialist",
        "role_id": 1526956760303140924,
        "tag": "[SUP. S]",
        "section": "🎧 Moderation & Support",
    },
    {
        "name": "Supporter",
        "role_id": 1526956795590086747,
        "tag": "[SUP]",
        "section": "🎧 Moderation & Support",
    },
    {
        "name": "Az. Supporter",
        "role_id": 1526956832822919331,
        "tag": "[Az. SUP]",
        "section": "🎧 Moderation & Support",
    },
]


ABSENCE_KEYWORDS = (
    "abgemeldet",
    "abwesen",
    "abwesenheit",
    "absence",
)


# ============================================================
# ACCESS
# ============================================================

async def ensure_dev(interaction: discord.Interaction) -> bool:
    if (
        interaction.guild is None
        or not isinstance(interaction.user, discord.Member)
    ):
        await interaction.response.send_message(
            "❌ Dieser Befehl kann nur auf dem Server benutzt werden.",
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
# RANK DETECTION
# ============================================================

def get_member_rank(member: discord.Member):
    member_role_ids = {role.id for role in member.roles}

    for rank in TEAM_RANKS:
        if rank["role_id"] in member_role_ids:
            return rank

    return None


def is_team_member(member: discord.Member) -> bool:
    return get_member_rank(member) is not None


# ============================================================
# ABSENCE
# ============================================================

def member_is_absent(member: discord.Member) -> bool:
    for role in member.roles:
        role_name = role.name.casefold()

        if any(keyword in role_name for keyword in ABSENCE_KEYWORDS):
            return True

    return False


# ============================================================
# NICKNAME CLEANING
# ============================================================

ALL_TEAM_TAGS = sorted(
    {rank["tag"] for rank in TEAM_RANKS},
    key=len,
    reverse=True,
)


def clean_member_name(member: discord.Member) -> str:
    name = member.nick or member.global_name or member.name

    name = re.sub(
        r"\s*-\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    for tag in ALL_TEAM_TAGS:
        if name.casefold().startswith(tag.casefold()):
            name = name[len(tag):].strip()
            break

    return name.strip() or member.name


def desired_nickname(member: discord.Member):
    rank = get_member_rank(member)

    if rank is None:
        return None

    base_name = clean_member_name(member)

    nickname = f"{rank['tag']} {base_name}"

    if member_is_absent(member):
        nickname += " - Abgemeldet"

    return nickname[:32]


# ============================================================
# NICKNAME SYNC
# ============================================================

async def sync_member_nickname(member: discord.Member) -> bool:
    if member.bot:
        return False

    guild = member.guild
    bot_member = guild.me

    if bot_member is None:
        return False

    if member.id == guild.owner_id:
        return False

    if member.top_role >= bot_member.top_role:
        print(
            f"⚠️ Nickname nicht änderbar: "
            f"{member} | Bot-Rolle zu niedrig"
        )
        return False

    rank = get_member_rank(member)

    # Kein Teamrang mehr
    if rank is None:
        if member.nick is None:
            return False

        cleaned = clean_member_name(member)

        if cleaned == member.nick:
            return False

        try:
            await member.edit(
                nick=cleaned[:32],
                reason="EHRP | System Teamrang entfernt",
            )
            return True

        except (discord.Forbidden, discord.HTTPException):
            return False

    wanted = desired_nickname(member)

    if not wanted:
        return False

    if member.nick == wanted:
        return False

    try:
        await member.edit(
            nick=wanted,
            reason=(
                f"EHRP | System Rang: {rank['name']} "
                f"| Tag: {rank['tag']}"
            ),
        )

        print(
            f"✅ Teamtag: {member.name} -> {wanted}"
        )

        return True

    except discord.Forbidden:
        print(
            f"⚠️ Keine Nickname-Berechtigung für {member}"
        )

    except discord.HTTPException as error:
        print(
            f"❌ Nickname Fehler {member}: {error}"
        )

    return False


# ============================================================
# TEAM MEMBERS
# ============================================================

def get_all_team_members(guild: discord.Guild):
    return [
        member
        for member in guild.members
        if not member.bot and is_team_member(member)
    ]


def members_for_rank(
    guild: discord.Guild,
    rank: dict,
):
    result = []

    for member in guild.members:
        if member.bot:
            continue

        member_rank = get_member_rank(member)

        if (
            member_rank is not None
            and member_rank["role_id"] == rank["role_id"]
        ):
            result.append(member)

    result.sort(
        key=lambda member: member.display_name.casefold()
    )

    return result


# ============================================================
# TEAM EMBED
# ============================================================

def build_team_embed(guild: discord.Guild):
    members = get_all_team_members(guild)

    absent_count = sum(
        1
        for member in members
        if member_is_absent(member)
    )

    active_count = len(members) - absent_count

    embed = discord.Embed(
        title="👥 EHRP | SYSTEM • TEAMLISTE",
        description=(
            "## OFFIZIELLE TEAMÜBERSICHT\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Teammitglieder:** {len(members)}\n"
            f"🟢 **Aktiv:** {active_count}\n"
            f"🏖️ **Abgemeldet:** {absent_count}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SYSTEM_COLOR,
    )

    sections = []

    for rank in TEAM_RANKS:
        if rank["section"] not in sections:
            sections.append(rank["section"])

    for section in sections:
        lines = []

        for rank in TEAM_RANKS:
            if rank["section"] != section:
                continue

            rank_members = members_for_rank(
                guild,
                rank,
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

                member_text = "\n".join(member_lines)

            else:
                member_text = "—"

            lines.append(
                f"**{rank['tag']} {rank['name']}**\n"
                f"{member_text}"
            )

        embed.add_field(
            name=section,
            value="\n\n".join(lines)[:1024],
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{TEAM_PANEL_MARKER} • "
            "Auto-Sync aktiv"
        )
    )

    return embed


# ============================================================
# FIND TEAM PANEL
# ============================================================

async def find_team_panel(guild: discord.Guild):
    bot_member = guild.me

    if bot_member is None:
        return None

    for channel in guild.text_channels:
        permissions = channel.permissions_for(bot_member)

        if not (
            permissions.view_channel
            and permissions.read_message_history
        ):
            continue

        try:
            async for message in channel.history(limit=50):
                if message.author.id != bot_member.id:
                    continue

                if not message.embeds:
                    continue

                footer = (
                    message.embeds[0].footer.text
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
# FULL SYNC
# ============================================================

async def perform_full_sync(guild: discord.Guild):
    changed = 0

    for member in guild.members:
        if member.bot:
            continue

        if await sync_member_nickname(member):
            changed += 1

    panel = await find_team_panel(guild)

    if panel:
        try:
            await panel.edit(
                embed=build_team_embed(guild)
            )

        except discord.HTTPException as error:
            print(
                f"❌ Team-Panel Update Fehler: {error}"
            )

    return changed


# ============================================================
# COG
# ============================================================

class Team(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_team_sync.start()

    def cog_unload(self):
        self.auto_team_sync.cancel()

    @tasks.loop(minutes=5)
    async def auto_team_sync(self):
        for guild in self.bot.guilds:
            try:
                await perform_full_sync(guild)

            except Exception as error:
                print(
                    f"❌ Team Auto-Sync Fehler: {error}"
                )

    @auto_team_sync.before_loop
    async def before_auto_team_sync(self):
        await self.bot.wait_until_ready()

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
            await sync_member_nickname(after)

            panel = await find_team_panel(
                after.guild
            )

            if panel:
                await panel.edit(
                    embed=build_team_embed(
                        after.guild
                    )
                )

        except Exception as error:
            print(
                f"❌ Team Member Update Fehler: {error}"
            )

    # ========================================================
    # /team_map
    # ========================================================

    @app_commands.command(
        name="team_map",
        description=(
            "Zeigt Teamrolle, Rollen-ID "
            "und den zugehörigen Nametag."
        ),
    )
    async def team_map(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        lines = []

        for rank in TEAM_RANKS:
            role = interaction.guild.get_role(
                rank["role_id"]
            )

            if role is None:
                lines.append(
                    (
                        f"❌ **{rank['name']}**\n"
                        f"↳ `{rank['role_id']}` "
                        f"→ {rank['tag']}"
                    )
                )
            else:
                lines.append(
                    (
                        f"✅ {role.mention}\n"
                        f"↳ **{rank['tag']}** "
                        f"• `{rank['role_id']}`"
                    )
                )

        embed = discord.Embed(
            title="🏷️ EHRP | ROLLE → NAMETAG",
            description="\n\n".join(lines)[:4000],
            color=SYSTEM_COLOR,
        )

        embed.set_footer(
            text=(
                "Feste Rollen-ID-Zuordnung"
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
            "Zeigt den aktuellen Status "
            "des Team-Systems."
        ),
    )
    async def team_status(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        members = get_all_team_members(
            interaction.guild
        )

        absent = sum(
            1
            for member in members
            if member_is_absent(member)
        )

        found_roles = sum(
            1
            for rank in TEAM_RANKS
            if interaction.guild.get_role(
                rank["role_id"]
            ) is not None
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
                f"🎭 **Rollen-IDs erkannt:** "
                f"{found_roles}/{len(TEAM_RANKS)}\n"
                "🔄 **Auto-Sync:** AKTIV\n"
                "⏱️ **Intervall:** 5 Minuten\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=SUCCESS_COLOR,
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
            "Synchronisiert alle Team-Nametags."
        ),
    )
    async def team_sync(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
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

        await interaction.followup.send(
            (
                "✅ **TEAM-SYNC ABGESCHLOSSEN**\n\n"
                f"👥 Teammitglieder erkannt: "
                f"**{len(members)}**\n"
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
            "Erstellt die automatische Teamliste."
        ),
    )
    async def team_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
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

        old_panel = await find_team_panel(
            interaction.guild
        )

        embed = build_team_embed(
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
                "✅ **Team-Panel erstellt**\n"
                f"📍 {new_message.channel.mention}"
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(
        Team(bot)
    )
