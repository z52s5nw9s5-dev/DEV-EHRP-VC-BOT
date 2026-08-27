from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks


# ============================================================
# EHRP | SYSTEM — RP CONTROL
# ============================================================

CONTROL_USER_ID = 1294267376459714621

RP_CHANNEL_ID = 1529998957449707551
BUERGER_ROLE_ID = 1526957918128443533

GERMAN_TIMEZONE = ZoneInfo("Europe/Berlin")


# ============================================================
# DESIGN
# ============================================================

START_COLOR = 0x57F287
STOP_COLOR = 0xED4245
SYSTEM_COLOR = 0x5865F2


# ============================================================
# BANNER
# ============================================================

BANNER_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "ehrp_banner.jpeg"
)


# ============================================================
# SETTINGS
# ============================================================

SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "rp_settings.json"
)

DEFAULT_SETTINGS = {
    "auto_enabled": False,
    "auto_time": "18:00",
    "rp_active": False,
    "last_auto_start": None,
}


# ============================================================
# SETTINGS LADEN
# ============================================================

def load_settings():
    settings = DEFAULT_SETTINGS.copy()

    if not SETTINGS_PATH.exists():
        return settings

    try:
        with SETTINGS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        settings.update(data)

    except Exception as error:
        print(
            f"⚠️ RP Settings konnten nicht geladen werden: {error}"
        )

    return settings


# ============================================================
# SETTINGS SPEICHERN
# ============================================================

def save_settings(settings):
    try:
        with SETTINGS_PATH.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                settings,
                file,
                indent=4,
                ensure_ascii=False,
            )

    except Exception as error:
        print(
            f"❌ RP Settings konnten nicht gespeichert werden: {error}"
        )


# ============================================================
# ZEIT
# ============================================================

def german_now():
    return datetime.now(
        GERMAN_TIMEZONE
    )


def parse_clock(value: str):
    try:
        parsed = datetime.strptime(
            value,
            "%H:%M",
        )

        return parsed.strftime(
            "%H:%M"
        )

    except ValueError:
        return None


# ============================================================
# BERECHTIGUNG
# ============================================================

async def check_control_permission(
    interaction: discord.Interaction,
):
    if interaction.user.id == CONTROL_USER_ID:
        return True

    await interaction.response.send_message(
        "❌ Du darfst das RP-System nicht steuern.",
        ephemeral=True,
    )

    return False


# ============================================================
# RP START EMBED
# ============================================================

def build_start_embed():
    now = german_now()

    embed = discord.Embed(
        title="🟢 SERVERSTART 🟢",
        description=(
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 **Der Server ist jetzt online.**\n\n"
            "🤝 **Kommt gerne drauf und erlebt gutes RP.**\n\n"
            "⭐ **Wir wünschen euch viel Spaß auf EHRP/VC.**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎭 **Das Roleplay ist offiziell gestartet.**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Euer EHRP/VC Serverteam**"
        ),
        color=START_COLOR,
        timestamp=now,
    )

    if BANNER_PATH.exists():
        embed.set_thumbnail(
            url="attachment://ehrp_banner.jpeg"
        )

    embed.set_footer(
        text=(
            "EHRP | System • RP Start • "
            f"{now.strftime('%H:%M')} Uhr"
        )
    )

    return embed


# ============================================================
# RP STOP EMBED
# ============================================================

def build_stop_embed():
    now = german_now()

    embed = discord.Embed(
        title="🛑 RP STOP 🛑",
        description=(
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛑 **Das Roleplay wurde beendet.**\n\n"
            "🚫 **Der offizielle RP-Betrieb ist ab sofort geschlossen.**\n\n"
            "🙏 **Vielen Dank an alle Bürger für das heutige Roleplay.**\n\n"
            "🌙 **Wir wünschen euch noch einen schönen Abend.**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⛔ **Bitte beendet laufende RP-Situationen ordentlich.**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Euer EHRP/VC Serverteam**"
        ),
        color=STOP_COLOR,
        timestamp=now,
    )

    if BANNER_PATH.exists():
        embed.set_thumbnail(
            url="attachment://ehrp_banner.jpeg"
        )

    embed.set_footer(
        text=(
            "EHRP | System • RP Stop • "
            f"{now.strftime('%H:%M')} Uhr"
        )
    )

    return embed


# ============================================================
# STATUS EMBED
# ============================================================

def build_status_embed(settings):
    rp_active = settings.get(
        "rp_active",
        False,
    )

    auto_enabled = settings.get(
        "auto_enabled",
        False,
    )

    auto_time = settings.get(
        "auto_time",
        "18:00",
    )

    embed = discord.Embed(
        title="🎮 EHRP | RP CONTROL",
        description=(
            "## ROLEPLAY STATUS\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{'🟢' if rp_active else '🔴'} "
            f"**RP:** "
            f"{'ONLINE' if rp_active else 'OFFLINE'}\n\n"

            f"{'🟢' if auto_enabled else '🔴'} "
            f"**Auto-Start:** "
            f"{'AN' if auto_enabled else 'AUS'}\n\n"

            f"🕒 **Startzeit:** {auto_time} Uhr\n\n"

            "🇩🇪 **Zeitzone:** Deutschland\n\n"

            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=(
            START_COLOR
            if rp_active
            else STOP_COLOR
        ),
    )

    embed.set_footer(
        text="EHRP | System • RP Control"
    )

    return embed


# ============================================================
# RP START SENDEN
# ============================================================

async def start_roleplay(
    bot: commands.Bot,
    settings,
):
    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        print(
            "❌ RP Channel nicht gefunden."
        )
        return False

    guild = channel.guild

    citizen_role = guild.get_role(
        BUERGER_ROLE_ID
    )

    if citizen_role:
        ping_text = (
            f"❤️ **Liebe {citizen_role.mention}**"
        )
    else:
        ping_text = (
            "❤️ **Liebe Bürger**"
        )

    embed = build_start_embed()

    allowed_mentions = discord.AllowedMentions(
        roles=True,
        users=False,
        everyone=False,
    )

    if BANNER_PATH.exists():
        file = discord.File(
            BANNER_PATH,
            filename="ehrp_banner.jpeg",
        )

        await channel.send(
            content=ping_text,
            embed=embed,
            file=file,
            allowed_mentions=allowed_mentions,
        )

    else:
        await channel.send(
            content=ping_text,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )

    settings["rp_active"] = True

    save_settings(
        settings
    )

    return True


# ============================================================
# RP STOP SENDEN
# ============================================================

async def stop_roleplay(
    bot: commands.Bot,
    settings,
):
    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        print(
            "❌ RP Channel nicht gefunden."
        )
        return False

    guild = channel.guild

    citizen_role = guild.get_role(
        BUERGER_ROLE_ID
    )

    if citizen_role:
        ping_text = (
            f"🛑 **Liebe {citizen_role.mention}**"
        )
    else:
        ping_text = (
            "🛑 **Liebe Bürger**"
        )

    embed = build_stop_embed()

    allowed_mentions = discord.AllowedMentions(
        roles=True,
        users=False,
        everyone=False,
    )

    if BANNER_PATH.exists():
        file = discord.File(
            BANNER_PATH,
            filename="ehrp_banner.jpeg",
        )

        await channel.send(
            content=ping_text,
            embed=embed,
            file=file,
            allowed_mentions=allowed_mentions,
        )

    else:
        await channel.send(
            content=ping_text,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )

    settings["rp_active"] = False

    save_settings(
        settings
    )

    return True


# ============================================================
# COG
# ============================================================

class RPControl(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

        self.settings = load_settings()

        self.auto_start_loop.start()


    def cog_unload(
        self,
    ):
        self.auto_start_loop.cancel()


    # ========================================================
    # AUTO START
    # ========================================================

    @tasks.loop(
        seconds=20
    )
    async def auto_start_loop(
        self,
    ):
        if not self.settings.get(
            "auto_enabled",
            False,
        ):
            return

        now = german_now()

        target_time = self.settings.get(
            "auto_time",
            "18:00",
        )

        current_time = now.strftime(
            "%H:%M"
        )

        if current_time != target_time:
            return

        today = now.strftime(
            "%Y-%m-%d"
        )

        if (
            self.settings.get(
                "last_auto_start"
            )
            == today
        ):
            return

        started = await start_roleplay(
            self.bot,
            self.settings,
        )

        if started:
            self.settings[
                "last_auto_start"
            ] = today

            save_settings(
                self.settings
            )

            print(
                f"✅ Automatischer RP-Start um {target_time} Uhr"
            )


    @auto_start_loop.before_loop
    async def before_auto_start(
        self,
    ):
        await self.bot.wait_until_ready()


    # ========================================================
    # /RP_STATUS
    # ========================================================

    @app_commands.command(
        name="rp_status",
        description="Zeigt den aktuellen RP-Status.",
    )
    async def rp_status(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.send_message(
            embed=build_status_embed(
                self.settings
            ),
            ephemeral=True,
        )


    # ========================================================
    # /RP_START
    # ========================================================

    @app_commands.command(
        name="rp_start",
        description="Sendet den RP-Start.",
    )
    async def rp_start(
        self,
        interaction: discord.Interaction,
    ):
        if not await check_control_permission(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        success = await start_roleplay(
            self.bot,
            self.settings,
        )

        if not success:
            await interaction.followup.send(
                "❌ RP-Start konnte nicht gesendet werden.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "🟢 **RP-Start wurde gesendet.**",
            ephemeral=True,
        )


    # ========================================================
    # /RP_STOP
    # ========================================================

    @app_commands.command(
        name="rp_stop",
        description="Sendet den RP-Stop.",
    )
    async def rp_stop(
        self,
        interaction: discord.Interaction,
    ):
        if not await check_control_permission(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        success = await stop_roleplay(
            self.bot,
            self.settings,
        )

        if not success:
            await interaction.followup.send(
                "❌ RP-Stop konnte nicht gesendet werden.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "🛑 **RP-Stop wurde gesendet.**",
            ephemeral=True,
        )


    # ========================================================
    # /RP_UHRZEIT
    # ========================================================

    @app_commands.command(
        name="rp_uhrzeit",
        description="Legt die automatische RP-Startzeit fest.",
    )
    @app_commands.describe(
        uhrzeit="Deutsche Uhrzeit, z.B. 18:30"
    )
    async def rp_uhrzeit(
        self,
        interaction: discord.Interaction,
        uhrzeit: str,
    ):
        if not await check_control_permission(
            interaction
        ):
            return

        parsed = parse_clock(
            uhrzeit
        )

        if parsed is None:
            await interaction.response.send_message(
                "❌ Bitte Format **HH:MM** benutzen, z.B. `18:30`.",
                ephemeral=True,
            )
            return

        self.settings[
            "auto_time"
        ] = parsed

        self.settings[
            "last_auto_start"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **RP-Startzeit geändert.**\n\n"
                f"🕒 **{parsed} Uhr**\n"
                "🇩🇪 Deutsche Zeit"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /RP_AUTO_AN
    # ========================================================

    @app_commands.command(
        name="rp_auto_an",
        description="Aktiviert den automatischen RP-Start.",
    )
    async def rp_auto_an(
        self,
        interaction: discord.Interaction,
    ):
        if not await check_control_permission(
            interaction
        ):
            return

        self.settings[
            "auto_enabled"
        ] = True

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "🟢 **Auto-RP aktiviert.**\n\n"
                f"🕒 Startzeit: **{self.settings['auto_time']} Uhr**\n"
                "🇩🇪 Deutsche Zeit"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /RP_AUTO_AUS
    # ========================================================

    @app_commands.command(
        name="rp_auto_aus",
        description="Deaktiviert den automatischen RP-Start.",
    )
    async def rp_auto_aus(
        self,
        interaction: discord.Interaction,
    ):
        if not await check_control_permission(
            interaction
        ):
            return

        self.settings[
            "auto_enabled"
        ] = False

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            "🔴 **Automatischer RP-Start deaktiviert.**",
            ephemeral=True,
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        RPControl(bot)
    )
