from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
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

RP_START_PING_ROLE_ID = 1526958031349350541

TIMEZONE = ZoneInfo("Europe/Berlin")

SETTINGS_FILE = "rp_settings.json"

BANNER_PATH = "assets/ehrp_banner.jpeg"

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C


# ============================================================
# KERNTEAM ODER HÖHER
# ============================================================

RP_CONTROL_ROLE_IDS = {
    1526952807838646334,  # Founder
    1526952825169510473,  # Co-Founder
    1526952877585596570,  # Obervorstand
    1526952894891556864,  # Vorstand
    1536099715412926584,  # Sachbearbeiter
    1526952911651995649,  # Verwaltungsleitung
    1526953865768075435,  # Hauptverwaltung
}


# ============================================================
# RP START TEXT
# ============================================================

RP_START_TEXT = """
RP START: <@&1526957918128443533>

**EHRP/VC – RP START**
Der RP-Server ist jetzt geöffnet!

Es ist soweit – EHRP/VC startet jetzt offiziell. Alle Einsatzkräfte, Zivilisten und Fraktionen können ab sofort beitreten und gemeinsam realistisches sowie hochwertiges Roleplay erleben.

Server beitreten:
Join Code: a3pu7mbc

Direkter Roblox-Join:
https://www.roblox.com/share?v=v2&code=5ihdm3h6q1r232

Wir erwarten von allen Spielern:
Realistisches und faires Roleplay
Einhaltung des Regelwerks
Respektvollen Umgang miteinander
Spaß am gemeinsamen RP

Wir freuen uns auf jeden einzelnen von euch und wünschen allen einen erfolgreichen Start auf EHRP/VC.

Das EHRP/VC-Team
""".strip()


# ============================================================
# RP STOP TEXT
# ============================================================

RP_STOP_TEXT = """
**EHRP/VC – RP STOP**
Der RP-Server wurde geschlossen.

Das heutige Roleplay ist beendet. Vielen Dank an alle Spieler, die dabei waren und zu einem gelungenen RP beigetragen haben.

Wir hoffen, ihr hattet Spaß und seid beim nächsten RP-Start wieder mit dabei.

Bleibt gerne auf dem Discord-Server, um keine Ankündigungen, Updates oder den nächsten RP-Start zu verpassen.

Vielen Dank für eure Teilnahme!

Euer EHRP/VC-Team

||Ping: <@&1526957918128443533>||
""".strip()


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "rp_active": False,
    "auto_enabled": False,
    "auto_hour": 20,
    "auto_minute": 0,
    "last_auto_start_date": None,
}


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)

        return settings

    except Exception as error:
        print(
            f"⚠️ RP Settings konnten nicht geladen werden: {error}"
        )

        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    try:
        with open(
            SETTINGS_FILE,
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
# ACCESS
# ============================================================

def can_control_rp(
    interaction: discord.Interaction,
) -> bool:

    if interaction.guild is None:
        return False

    if interaction.user.id == CONTROL_USER_ID:
        return True

    if not isinstance(
        interaction.user,
        discord.Member,
    ):
        return False

    return any(
        role.id in RP_CONTROL_ROLE_IDS
        for role in interaction.user.roles
    )


async def check_control_access(
    interaction: discord.Interaction,
) -> bool:

    if can_control_rp(interaction):
        return True

    message = (
        "❌ Du darfst die RP-Steuerung nicht benutzen.\n"
        "Diese Funktion ist nur für das **Kernteam oder höher** freigeschaltet."
    )

    if interaction.response.is_done():
        await interaction.followup.send(
            message,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            message,
            ephemeral=True,
        )

    return False


# ============================================================
# BANNER
# ============================================================

def banner_exists() -> bool:
    return os.path.exists(
        BANNER_PATH
    )


def get_banner_file():
    if not banner_exists():
        return None

    return discord.File(
        BANNER_PATH,
        filename="ehrp_banner.jpeg",
    )


# ============================================================
# EMBEDS
# ============================================================

def build_start_embed() -> discord.Embed:
    embed = discord.Embed(
        description=RP_START_TEXT,
        color=SUCCESS_COLOR,
        timestamp=datetime.now(
            TIMEZONE
        ),
    )

    embed.set_author(
        name="EHRP | SYSTEM"
    )

    if banner_exists():
        embed.set_image(
            url="attachment://ehrp_banner.jpeg"
        )

    embed.set_footer(
        text="EHRP/VC • RP Control"
    )

    return embed


def build_stop_embed() -> discord.Embed:
    embed = discord.Embed(
        description=RP_STOP_TEXT,
        color=ERROR_COLOR,
        timestamp=datetime.now(
            TIMEZONE
        ),
    )

    embed.set_author(
        name="EHRP | SYSTEM"
    )

    if banner_exists():
        embed.set_image(
            url="attachment://ehrp_banner.jpeg"
        )

    embed.set_footer(
        text="EHRP/VC • RP Control"
    )

    return embed


# ============================================================
# COG
# ============================================================

class RPControl(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot
        self.settings = load_settings()

        self.auto_rp_loop.start()


    def cog_unload(self):
        self.auto_rp_loop.cancel()


    # ========================================================
    # CHANNEL
    # ========================================================

    def get_rp_channel(self):
        return self.bot.get_channel(
            RP_CHANNEL_ID
        )


    # ========================================================
    # SEND START
    # ========================================================

    async def send_rp_start(self):

        channel = self.get_rp_channel()

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            raise RuntimeError(
                "RP-Channel wurde nicht gefunden."
            )

        embed = build_start_embed()

        ping_content = (
            f"<@&{RP_START_PING_ROLE_ID}>"
        )

        file = get_banner_file()

        kwargs = {
            "content": ping_content,
            "embed": embed,
            "allowed_mentions":
                discord.AllowedMentions(
                    roles=True,
                    users=False,
                    everyone=False,
                ),
        }

        if file is not None:
            kwargs["file"] = file

        message = await channel.send(
            **kwargs
        )

        self.settings[
            "rp_active"
        ] = True

        save_settings(
            self.settings
        )

        return message


    # ========================================================
    # SEND STOP
    # ========================================================

    async def send_rp_stop(self):

        channel = self.get_rp_channel()

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            raise RuntimeError(
                "RP-Channel wurde nicht gefunden."
            )

        embed = build_stop_embed()

        file = get_banner_file()

        kwargs = {
            "embed": embed,
            "allowed_mentions":
                discord.AllowedMentions(
                    roles=True,
                    users=False,
                    everyone=False,
                ),
        }

        if file is not None:
            kwargs["file"] = file

        message = await channel.send(
            **kwargs
        )

        self.settings[
            "rp_active"
        ] = False

        save_settings(
            self.settings
        )

        return message


    # ========================================================
    # /RP_START
    # ========================================================

    @app_commands.command(
        name="rp_start",
        description="Startet das EHRP/VC Roleplay.",
    )
    async def rp_start(
        self,
        interaction: discord.Interaction,
    ):

        if not await check_control_access(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            message = await self.send_rp_start()

        except Exception as error:
            print(
                f"❌ RP Start Fehler: {error}"
            )

            await interaction.followup.send(
                "❌ Der RP-Start konnte nicht gesendet werden.",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            (
                "✅ **RP wurde gestartet.**\n"
                f"➡️ {message.jump_url}"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /RP_STOP
    # ========================================================

    @app_commands.command(
        name="rp_stop",
        description="Beendet das EHRP/VC Roleplay.",
    )
    async def rp_stop(
        self,
        interaction: discord.Interaction,
    ):

        if not await check_control_access(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            message = await self.send_rp_stop()

        except Exception as error:
            print(
                f"❌ RP Stop Fehler: {error}"
            )

            await interaction.followup.send(
                "❌ Der RP-Stop konnte nicht gesendet werden.",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            (
                "✅ **RP wurde beendet.**\n"
                f"➡️ {message.jump_url}"
            ),
            ephemeral=True,
        )


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

        if not await check_control_access(
            interaction
        ):
            return

        rp_active = self.settings.get(
            "rp_active",
            False,
        )

        auto_enabled = self.settings.get(
            "auto_enabled",
            False,
        )

        auto_hour = self.settings.get(
            "auto_hour",
            20,
        )

        auto_minute = self.settings.get(
            "auto_minute",
            0,
        )

        if rp_active:
            rp_text = "🟢 RP läuft"
            color = SUCCESS_COLOR
        else:
            rp_text = "🔴 RP geschlossen"
            color = ERROR_COLOR

        if auto_enabled:
            auto_text = (
                "🟢 Aktiv\n"
                f"⏰ {auto_hour:02d}:{auto_minute:02d} Uhr"
            )
        else:
            auto_text = "🔴 Deaktiviert"

        embed = discord.Embed(
            title="⚙️ EHRP | RP CONTROL",
            description=(
                "## SYSTEM STATUS\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"**RP:** {rp_text}\n\n"
                f"**Auto RP:** {auto_text}\n\n"
                "🕒 **Zeitzone:** Europe/Berlin\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            color=color,
            timestamp=datetime.now(
                TIMEZONE
            ),
        )

        embed.set_footer(
            text="EHRP | System • RP Control"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


    # ========================================================
    # /RP_UHRZEIT
    # ========================================================

    @app_commands.command(
        name="rp_uhrzeit",
        description="Stellt die automatische RP-Startzeit ein.",
    )
    @app_commands.describe(
        stunde="Stunde von 0 bis 23",
        minute="Minute von 0 bis 59",
    )
    async def rp_uhrzeit(
        self,
        interaction: discord.Interaction,
        stunde: app_commands.Range[int, 0, 23],
        minute: app_commands.Range[int, 0, 59] = 0,
    ):

        if not await check_control_access(
            interaction
        ):
            return

        self.settings[
            "auto_hour"
        ] = int(stunde)

        self.settings[
            "auto_minute"
        ] = int(minute)

        self.settings[
            "last_auto_start_date"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **Automatische RP-Uhrzeit geändert**\n\n"
                f"⏰ Neue Uhrzeit: "
                f"**{stunde:02d}:{minute:02d} Uhr**\n"
                "🇩🇪 Zeitzone: Europe/Berlin"
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

        if not await check_control_access(
            interaction
        ):
            return

        self.settings[
            "auto_enabled"
        ] = True

        save_settings(
            self.settings
        )

        hour = self.settings.get(
            "auto_hour",
            20,
        )

        minute = self.settings.get(
            "auto_minute",
            0,
        )

        await interaction.response.send_message(
            (
                "✅ **Automatischer RP-Start aktiviert**\n\n"
                f"⏰ Startzeit: "
                f"**{hour:02d}:{minute:02d} Uhr**\n"
                "🇩🇪 Zeitzone: Europe/Berlin"
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

        if not await check_control_access(
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
            "✅ **Automatischer RP-Start deaktiviert.**",
            ephemeral=True,
        )


    # ========================================================
    # AUTO RP LOOP
    # ========================================================

    @tasks.loop(
        seconds=20
    )
    async def auto_rp_loop(self):

        if not self.settings.get(
            "auto_enabled",
            False,
        ):
            return

        now = datetime.now(
            TIMEZONE
        )

        hour = self.settings.get(
            "auto_hour",
            20,
        )

        minute = self.settings.get(
            "auto_minute",
            0,
        )

        today = now.strftime(
            "%Y-%m-%d"
        )

        last_start = self.settings.get(
            "last_auto_start_date"
        )

        if (
            now.hour != hour
            or now.minute != minute
        ):
            return

        if last_start == today:
            return

        try:
            await self.send_rp_start()

            self.settings[
                "last_auto_start_date"
            ] = today

            save_settings(
                self.settings
            )

            print(
                "✅ Automatischer RP-Start gesendet: "
                f"{today} {hour:02d}:{minute:02d}"
            )

        except Exception as error:
            print(
                "❌ Automatischer RP-Start Fehler: "
                f"{error}"
            )


    @auto_rp_loop.before_loop
    async def before_auto_rp_loop(self):

        await self.bot.wait_until_ready()

        await asyncio.sleep(3)


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        RPControl(bot)
    )
