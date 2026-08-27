from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks


# ============================================================
# EHRP | SYSTEM — CONTROL CENTER
# ============================================================

CONTROL_USER_ID = 1294267376459714621

DASHBOARD_CHANNEL_ID = 1542358230053691534

GERMAN_TZ = ZoneInfo("Europe/Berlin")

SYSTEM_COLOR = 0x5865F2
ONLINE_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C


# ============================================================
# RP
# ============================================================

RP_SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "rp_settings.json"
)


def load_rp_settings():
    default = {
        "auto_enabled": False,
        "auto_time": "18:00",
        "rp_active": False,
    }

    if not RP_SETTINGS_PATH.exists():
        return default

    try:
        with RP_SETTINGS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        default.update(data)

    except Exception:
        pass

    return default


# ============================================================
# TEAM ROLE IDS
# ============================================================

TEAM_ROLE_IDS = [
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
]


# ============================================================
# TICKET CATEGORIES
# ============================================================

TICKET_CATEGORY_IDS = [
    1526978181591207986,
    1526938849618432000,
    1526938782732124201,
    1526938582772875404,
    1526938931013222570,
    1526980142054903969,
    1526982043009941564,
]


# ============================================================
# SELF ROLES
# ============================================================

SELF_ROLE_IDS = [
    1526957986696921162,
    1526958031349350541,
    1526958087892631632,
    1526958107568377987,
    1526958133233193031,
]


# ============================================================
# HELPERS
# ============================================================

def count_team_members(
    guild: discord.Guild,
):
    role_ids = set(
        TEAM_ROLE_IDS
    )

    members = set()

    for member in guild.members:

        if member.bot:
            continue

        if any(
            role.id in role_ids
            for role in member.roles
        ):
            members.add(
                member.id
            )

    return len(
        members
    )


def count_open_tickets(
    guild: discord.Guild,
):
    total = 0

    for category_id in TICKET_CATEGORY_IDS:

        category = guild.get_channel(
            category_id
        )

        if not isinstance(
            category,
            discord.CategoryChannel,
        ):
            continue

        for channel in category.text_channels:

            if (
                channel.topic
                and channel.topic.startswith(
                    "EHRP_TICKET|"
                )
            ):
                total += 1

    return total


def count_selfroles(
    guild: discord.Guild,
):
    return sum(
        1
        for role_id in SELF_ROLE_IDS
        if guild.get_role(
            role_id
        )
        is not None
    )


# ============================================================
# DASHBOARD EMBED
# ============================================================

def build_dashboard(
    guild: discord.Guild,
    bot: commands.Bot,
):
    now = datetime.now(
        GERMAN_TZ
    )

    rp = load_rp_settings()

    rp_active = rp.get(
        "rp_active",
        False,
    )

    auto_enabled = rp.get(
        "auto_enabled",
        False,
    )

    auto_time = rp.get(
        "auto_time",
        "18:00",
    )

    team_count = count_team_members(
        guild
    )

    ticket_count = count_open_tickets(
        guild
    )

    selfrole_count = count_selfroles(
        guild
    )

    embed = discord.Embed(
        title="⚙️ EHRP | SYSTEM CONTROL CENTER",
        description=(
            "## LIVE SYSTEM STATUS\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🤖 **SYSTEM**\n"
            "🟢 Bot: **ONLINE**\n"
            f"🌐 Server: **{guild.name}**\n\n"

            "🎮 **ROLEPLAY**\n"
            f"{'🟢' if rp_active else '🔴'} RP: "
            f"**{'ONLINE' if rp_active else 'OFFLINE'}**\n"
            f"{'🟢' if auto_enabled else '🔴'} Auto-RP: "
            f"**{'AN' if auto_enabled else 'AUS'}**\n"
            f"🕒 Auto-Start: **{auto_time} Uhr**\n\n"

            "👥 **TEAM**\n"
            f"🟢 Erkannte Teammitglieder: "
            f"**{team_count}**\n\n"

            "🎫 **TICKETS**\n"
            f"{'🟡' if ticket_count else '🟢'} "
            f"Offene Tickets: **{ticket_count}**\n\n"

            "🔔 **SELF ROLES**\n"
            f"{'🟢' if selfrole_count == 5 else '🟡'} "
            f"Rollen verfügbar: "
            f"**{selfrole_count}/5**\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🇩🇪 Letztes Update: "
            f"**{now.strftime('%H:%M:%S')} Uhr**"
        ),
        color=(
            ONLINE_COLOR
            if selfrole_count == 5
            else WARNING_COLOR
        ),
        timestamp=now,
    )

    if bot.user:
        embed.set_thumbnail(
            url=bot.user.display_avatar.url
        )

    embed.set_footer(
        text=(
            "EHRP | System • "
            "Live Control Center • Auto-Update"
        )
    )

    return embed


# ============================================================
# PERMISSION
# ============================================================

async def owner_only(
    interaction: discord.Interaction,
):
    if (
        interaction.user.id
        == CONTROL_USER_ID
    ):
        return True

    await interaction.response.send_message(
        "❌ Dieses Control Center darfst du nicht steuern.",
        ephemeral=True,
    )

    return False


# ============================================================
# BUTTONS
# ============================================================

class SystemDashboardView(
    discord.ui.View
):
    def __init__(
        self,
    ):
        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Aktualisieren",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:dashboard:refresh",
    )
    async def refresh(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await owner_only(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        await interaction.message.edit(
            embed=build_dashboard(
                interaction.guild,
                interaction.client,
            ),
            view=self,
        )

        await interaction.followup.send(
            "✅ Dashboard aktualisiert.",
            ephemeral=True,
        )


    @discord.ui.button(
        label="RP Status",
        emoji="🎮",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:dashboard:rp",
    )
    async def rp_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await owner_only(
            interaction
        ):
            return

        rp = load_rp_settings()

        await interaction.response.send_message(
            (
                "🎮 **RP STATUS**\n\n"
                f"RP: **{'ONLINE' if rp.get('rp_active') else 'OFFLINE'}**\n"
                f"Auto-RP: **{'AN' if rp.get('auto_enabled') else 'AUS'}**\n"
                f"Startzeit: **{rp.get('auto_time', '18:00')} Uhr**"
            ),
            ephemeral=True,
        )


    @discord.ui.button(
        label="Team",
        emoji="👥",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:dashboard:team",
    )
    async def team_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await owner_only(
            interaction
        ):
            return

        count = count_team_members(
            interaction.guild
        )

        await interaction.response.send_message(
            f"👥 Erkannte Teammitglieder: **{count}**",
            ephemeral=True,
        )


    @discord.ui.button(
        label="Tickets",
        emoji="🎫",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:dashboard:tickets",
    )
    async def ticket_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await owner_only(
            interaction
        ):
            return

        count = count_open_tickets(
            interaction.guild
        )

        await interaction.response.send_message(
            f"🎫 Offene Tickets: **{count}**",
            ephemeral=True,
        )


    @discord.ui.button(
        label="Self Roles",
        emoji="🔔",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:dashboard:selfroles",
    )
    async def selfroles_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await owner_only(
            interaction
        ):
            return

        count = count_selfroles(
            interaction.guild
        )

        await interaction.response.send_message(
            f"🔔 Self-Roles verfügbar: **{count}/5**",
            ephemeral=True,
        )


# ============================================================
# COG
# ============================================================

class SystemDashboard(
    commands.Cog
):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        bot.add_view(
            SystemDashboardView()
        )

        self.dashboard_loop.start()


    def cog_unload(
        self,
    ):
        self.dashboard_loop.cancel()


    # ========================================================
    # AUTOMATISCH ALLE 60 SEKUNDEN AKTUALISIEREN
    # ========================================================

    @tasks.loop(
        seconds=60
    )
    async def dashboard_loop(
        self,
    ):
        for guild in self.bot.guilds:

            channel = guild.get_channel(
                DASHBOARD_CHANNEL_ID
            )

            if not isinstance(
                channel,
                discord.TextChannel,
            ):
                continue

            message = await self.find_dashboard(
                channel
            )

            if message is None:
                continue

            try:
                await message.edit(
                    embed=build_dashboard(
                        guild,
                        self.bot,
                    ),
                    view=SystemDashboardView(),
                )

            except discord.HTTPException:
                pass


    @dashboard_loop.before_loop
    async def before_dashboard_loop(
        self,
    ):
        await self.bot.wait_until_ready()


    # ========================================================
    # DASHBOARD FINDEN
    # ========================================================

    async def find_dashboard(
        self,
        channel: discord.TextChannel,
    ):
        try:
            async for message in channel.history(
                limit=25
            ):
                if (
                    self.bot.user
                    and message.author.id
                    == self.bot.user.id
                    and message.embeds
                    and message.embeds[0].title
                    == "⚙️ EHRP | SYSTEM CONTROL CENTER"
                ):
                    return message

        except discord.HTTPException:
            pass

        return None


    # ========================================================
    # /system_panel
    # ========================================================

    @app_commands.command(
        name="system_panel",
        description=(
            "Erstellt das dauerhafte "
            "EHRP System Control Center."
        ),
    )
    async def system_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not await owner_only(
            interaction
        ):
            return

        channel = interaction.guild.get_channel(
            DASHBOARD_CHANNEL_ID
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Dashboard-Channel wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        existing = await self.find_dashboard(
            channel
        )

        if existing:
            await existing.edit(
                embed=build_dashboard(
                    interaction.guild,
                    self.bot,
                ),
                view=SystemDashboardView(),
            )

            await interaction.followup.send(
                (
                    "✅ Control Center aktualisiert.\n"
                    f"📍 {channel.mention}"
                ),
                ephemeral=True,
            )

            return

        await channel.send(
            embed=build_dashboard(
                interaction.guild,
                self.bot,
            ),
            view=SystemDashboardView(),
        )

        await interaction.followup.send(
            (
                "✅ **Control Center dauerhaft erstellt.**\n"
                f"📍 {channel.mention}\n\n"
                "Es aktualisiert sich jetzt automatisch."
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
        SystemDashboard(bot)
    )
