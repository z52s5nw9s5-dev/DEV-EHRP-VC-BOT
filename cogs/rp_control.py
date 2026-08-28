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
RP_START_PING_ROLE_ID = 1526958031349350541

GERMAN_TIMEZONE = ZoneInfo("Europe/Berlin")


# ============================================================
# DESIGN
# ============================================================

START_COLOR = 0x57F287
STOP_COLOR = 0xED4245


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
        description=(
            "**EHRP/VC – RP START**\n"
            "Der RP-Server ist jetzt geöffnet!\n\n"

            "Es ist soweit – EHRP/VC startet jetzt offiziell. "
            "Alle Einsatzkräfte, Zivilisten und Fraktionen können "
            "ab sofort beitreten und gemeinsam realistisches sowie "
            "hochwertiges Roleplay erleben.\n\n"

            "Server beitreten:\n"
            "Join Code: a3pu7mbc\n\n"

            "Direkter Roblox-Join:\n"
            "https://www.roblox.com/share?v=v2&code=5ihdm3h6q1r232\n\n"

            "Wir erwarten von allen Spielern:\n"
            "Realistisches und faires Roleplay\n"
            "Einhaltung des Regelwerks\n"
            "Respektvollen Umgang miteinander\n"
            "Spaß am gemeinsamen RP\n\n"

            "Wir freuen uns auf jeden einzelnen von euch und wünschen "
            "allen einen erfolgreichen Start auf EHRP/VC.\n\n"

            "Das EHRP/VC-Team"
        ),
        color=START_COLOR,
        timestamp=now,
    )

    if BANNER_PATH.exists():
        embed.set_image(
            url="attachment://ehrp_banner.jpeg"
        )

    return embed


# ============================================================
# RP STOP EMBED
# ============================================================

def build_stop_embed():
    now = german_now()

    embed = discord.Embed(
        description=(
            "**EHRP/VC – RP STOP**\n"
            "Der RP-Server wurde geschlossen.\n\n"

            "Das heutige Roleplay ist beendet. Vielen Dank an alle "
            "Spieler, die dabei waren und zu einem gelungenen RP "
            "beigetragen haben.\n\n"

            "Wir hoffen, ihr hattet Spaß und seid beim nächsten "
            "RP-Start wieder mit dabei.\n\n"

            "Bleibt gerne auf dem Discord-Server, um keine "
            "Ankündigungen, Updates oder den nächsten RP-Start "
            "zu verpassen.\n\n"

            "Vielen Dank für eure Teilnahme!\n\n"

            "Euer EHRP/VC-Team\n\n"

            "||Ping: <@&1526957918128443533>||"
        ),
        color=STOP_COLOR,
        timestamp=now,
    )

    if BANNER_PATH.exists():
        embed.set_image(
            url="attachment://ehrp_banner.jpeg"
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

    rp_start_role = guild.get_role(
        RP_START_PING_ROLE_ID
    )

    lines = []

    if citizen_role:
        lines.append(
            citizen_role.mention
        )
    else:
        lines.append(
            "<@&1526957918128443533>"
        )

    if rp_start_role:
        lines.append(
            rp_start_role.mention
        )

    ping_text = "\n".join(
        lines
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
            embed=embed,
            file=file,
            allowed_mentions=allowed_mentions,
        )

    else:
        await channel.send(
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

        if success:
            await interaction.followup.send(
                "🟢 **RP-Start wurde gesendet.**",
                ephemeral=True,
            )

        else:
            await interaction.followup.send(
                "❌ RP-Start konnte nicht gesendet werden.",
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

        if success:
            await interaction.followup.send(
                "🛑 **RP-Stop wurde gesendet.**",
                ephemeral=True,
            )

        else:
            await interaction.followup.send(
                "❌ RP-Stop konnte nicht gesendet werden.",
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
                f"🕒 Startzeit: "
                f"**{self.settings['auto_time']} Uhr**\n"
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
