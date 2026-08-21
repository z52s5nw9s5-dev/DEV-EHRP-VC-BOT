from __future__ import annotations

import re
import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.checks import ensure_dev


# =========================================================
# EHRP | SYSTEM — TEAM CONFIG
# Reihenfolge = Rangfolge von oben nach unten
# =========================================================

TEAM_STRUCTURE = [
    (
        "👑 Leitung",
        [
            ("Founder", "[FD]"),
            ("Co-Founder", "[Co. FD]"),
        ],
    ),
    (
        "🏛️ Leaderebene",
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
        "⚙️ Teamverwaltung",
        [
            ("Head of Management", "[HoM]"),
            ("Sr. Management", "[Sr. M]"),
            ("Manager", "[M]"),
            ("Stv. Manager", "[Stv. M]"),
        ],
    ),
    (
        "🛡️ Management",
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
        "🎫 Moderatoren",
        [
            ("Support-Spezialist", "[SUP. S]"),
            ("Supporter", "[SUP]"),
            ("Az. Supporter", "[Az. SUP]"),
        ],
    ),
]


# Galaxy kann seine Rolle unterschiedlich nennen.
# Sobald eine Rolle eines Mitglieds eines dieser Wörter enthält,
# behandelt EHRP | System die Person als abgemeldet.
ABSENCE_KEYWORDS = (
    "abgemeldet",
    "abwesen",
    "absence",
)


# Namen, die niemals als "Grundname" übrig bleiben sollen.
PREFIX_PATTERN = re.compile(
    r"^\s*(?:\[[^\]]+\]\s*)+",
    flags=re.IGNORECASE,
)


def normalize(text: str) -> str:
    return (
        text.lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
        .strip()
    )


def find_role(guild: discord.Guild, wanted_name: str):
    """
    Findet eine Rolle möglichst tolerant.
    Exakte Schreibweise ist bevorzugt.
    """
    exact = discord.utils.get(guild.roles, name=wanted_name)

    if exact:
        return exact

    target = normalize(wanted_name)

    for role in guild.roles:
        if normalize(role.name) == target:
            return role

    return None


def is_absent(member: discord.Member) -> bool:
    for role in member.roles:
        role_name = role.name.lower()

        if any(keyword in role_name for keyword in ABSENCE_KEYWORDS):
            return True

    return False


def base_member_name(member: discord.Member) -> str:
    """
    Entfernt vorhandene Team-Kürzel vom Anfang des Nicknames.
    """
    name = member.nick or member.global_name or member.name

    name = PREFIX_PATTERN.sub("", name).strip()

    # Alten Abwesenheitszusatz entfernen.
    name = re.sub(
        r"\s*[-|•]\s*abgemeldet\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    return name.strip()


def get_highest_team_rank(member: discord.Member):
    """
    Gibt nur den höchsten gefundenen Teamrang zurück.
    """
    role_names = {normalize(role.name) for role in member.roles}

    for _, ranks in TEAM_STRUCTURE:
        for role_name, prefix in ranks:
            if normalize(role_name) in role_names:
                return role_name, prefix

    return None


def member_has_team_role(member: discord.Member) -> bool:
    return get_highest_team_rank(member) is not None


def desired_nickname(member: discord.Member):
    rank = get_highest_team_rank(member)

    if rank is None:
        return None

    _, prefix = rank
    name = base_member_name(member)

    new_name = f"{prefix} {name}"

    if is_absent(member):
        new_name += " - Abgemeldet"

    # Discord Nicknames maximal 32 Zeichen.
    return new_name[:32]


async def update_member_nickname(member: discord.Member):
    if member.bot:
        return

    desired = desired_nickname(member)

    if desired is None:
        return

    current = member.nick or member.global_name or member.name

    if current == desired:
        return

    try:
        await member.edit(
            nick=desired,
            reason="EHRP | System — automatische Team-Synchronisation",
        )
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass


def members_for_role(guild: discord.Guild, role_name: str):
    role = find_role(guild, role_name)

    if role is None:
        return []

    members = [
        member
        for member in role.members
        if not member.bot
    ]

    return sorted(
        members,
        key=lambda m: (
            m.display_name.lower(),
            m.id,
        ),
    )


def build_team_embed(guild: discord.Guild):
    embed = discord.Embed(
        title="👥 EHRP | SYSTEM • Teamliste",
        description=(
            "Alle Teammitglieder werden automatisch anhand "
            "ihrer Discord-Rollen erkannt.\n\n"
            "🔄 Rollen- und Teamänderungen werden automatisch synchronisiert."
        ),
        color=discord.Color.blurple(),
    )

    total_members = set()

    for section_name, ranks in TEAM_STRUCTURE:
        lines = []

        for role_name, prefix in ranks:
            members = members_for_role(guild, role_name)

            for member in members:
                total_members.add(member.id)

            lines.append(f"**{role_name}**")

            if members:
                for member in members:
                    absence = " `ABG`" if is_absent(member) else ""
                    lines.append(
                        f"└ {member.mention}{absence}"
                    )
            else:
                lines.append("└ *Keine Mitglieder*")

            lines.append("")

        value = "\n".join(lines).strip()

        if len(value) > 1024:
            value = value[:1021] + "..."

        embed.add_field(
            name=section_name,
            value=value,
            inline=False,
        )

    embed.set_footer(
        text=(
            f"EHRP | System • {len(total_members)} Teammitglieder "
            "• automatische Synchronisation"
        )
    )

    return embed


def find_team_channel(guild: discord.Guild):
    """
    Sucht automatisch nach dem Teamlisten-Channel.
    """
    candidates = []

    for channel in guild.text_channels:
        clean = normalize(channel.name)

        if "teamliste" in clean:
            return channel

        if "team" in clean and "liste" in clean:
            candidates.append(channel)

    return candidates[0] if candidates else None


async def find_existing_team_message(
    channel: discord.TextChannel,
    bot_user: discord.ClientUser,
):
    try:
        async for message in channel.history(limit=50):
            if message.author.id != bot_user.id:
                continue

            if not message.embeds:
                continue

            embed = message.embeds[0]

            if embed.title and "Teamliste" in embed.title:
                return message

    except discord.Forbidden:
        return None

    return None


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.team_sync_loop.start()

    def cog_unload(self):
        self.team_sync_loop.cancel()

    # =====================================================
    # AUTOMATISCHE ROLLEN-/NICKNAME-ÄNDERUNGEN
    # =====================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):
        if before.roles != after.roles:
            await update_member_nickname(after)

            await self.refresh_teamlist(after.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await update_member_nickname(member)

    # =====================================================
    # PERIODISCHER SELBST-CHECK
    # =====================================================

    @tasks.loop(minutes=5)
    async def team_sync_loop(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member_has_team_role(member):
                    await update_member_nickname(member)

            await self.refresh_teamlist(guild)

    @team_sync_loop.before_loop
    async def before_team_sync_loop(self):
        await self.bot.wait_until_ready()

    # =====================================================
    # TEAMLISTE
    # =====================================================

    async def refresh_teamlist(self, guild: discord.Guild):
        channel = find_team_channel(guild)

        if channel is None:
            return

        embed = build_team_embed(guild)

        message = await find_existing_team_message(
            channel,
            self.bot.user,
        )

        try:
            if message:
                await message.edit(embed=embed)
            else:
                await channel.send(embed=embed)

        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    # =====================================================
    # MANUELLER SYNC
    # =====================================================

    @app_commands.command(
        name="team_sync",
        description="Synchronisiert Teamliste und Team-Nicknames.",
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

        changed = 0

        for member in interaction.guild.members:
            if not member_has_team_role(member):
                continue

            before = member.nick

            await update_member_nickname(member)

            if member.nick != before:
                changed += 1

        await self.refresh_teamlist(
            interaction.guild
        )

        await interaction.followup.send(
            (
                "✅ **EHRP | System synchronisiert**\n\n"
                f"👥 Teamliste aktualisiert\n"
                f"🏷️ Nicknames geprüft: "
                f"**{changed} Änderungen**"
            ),
            ephemeral=True,
        )

    # =====================================================
    # TEAM STATUS
    # =====================================================

    @app_commands.command(
        name="team_status",
        description="Zeigt den Status des Team-Systems.",
    )
    async def team_status(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_dev(interaction):
            return

        total = 0
        absent = 0

        for member in interaction.guild.members:
            if member_has_team_role(member):
                total += 1

                if is_absent(member):
                    absent += 1

        await interaction.response.send_message(
            (
                "⚙️ **EHRP | SYSTEM • TEAM STATUS**\n\n"
                f"👥 Teammitglieder: **{total}**\n"
                f"🏖️ Abgemeldet: **{absent}**\n"
                f"🟢 Aktiv: **{total - absent}**\n\n"
                "🔄 Auto-Sync: **AKTIV**"
            ),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Team(bot))