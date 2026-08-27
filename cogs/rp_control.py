from __future__ import annotations

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

OWNER_USER_ID = 1294267376459714621

RP_CHANNEL_ID = 1529998957449707551
RP_ROLE_ID = 1526957918128443533

GERMAN_TZ = ZoneInfo("Europe/Berlin")

SETTINGS_FILE = "rp_settings.json"

DEFAULT_SETTINGS = {
    "auto_enabled": False,
    "auto_time": "18:00",
    "rp_active": False,
    "last_auto_date": None,
}

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C


# ============================================================
# SETTINGS
# ============================================================

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        result = DEFAULT_SETTINGS.copy()
        result.update(data)

        return result

    except Exception as error:
        print(
            f"❌ RP Settings Load Fehler: {error}"
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
            f"❌ RP Settings Save Fehler: {error}"
        )


# ============================================================
# ACCESS
# ============================================================

async def ensure_rp_owner(
    interaction: discord.Interaction,
) -> bool:

    if interaction.user.id == OWNER_USER_ID:
        return True

    await interaction.response.send_message(
        "❌ Du darfst das RP-System nicht steuern.",
        ephemeral=True,
    )

    return False


# ============================================================
# HELPERS
# ============================================================

def parse_time(
    value: str,
):
    value = value.strip()

    try:
        parsed = datetime.strptime(
            value,
            "%H:%M",
        )

        return parsed.hour, parsed.minute

    except ValueError:
        return None


def get_german_time() -> datetime:
    return datetime.now(
        GERMAN_TZ
    )


def build_status_embed(
    settings: dict,
):
    now = get_german_time()

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
            "## SYSTEM STATUS\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"{'🟢' if rp_active else '🔴'} "
            f"**RP-Status:** "
            f"{'ONLINE' if rp_active else 'OFFLINE'}\n"
            f"{'🟢' if auto_enabled else '🔴'} "
            f"**Auto-RP:** "
            f"{'AN' if auto_enabled else 'AUS'}\n"
            f"🕒 **Auto-Start:** `{auto_time}`\n"
            f"🇩🇪 **Zeitzone:** Europe/Berlin\n"
            f"⌚ **Aktuell:** "
            f"`{now.strftime('%H:%M:%S')}`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=(
            SUCCESS_COLOR
            if rp_active
            else SYSTEM_COLOR
        ),
        timestamp=now,
    )

    embed.set_footer(
        text="EHRP | System • RP Control"
    )

    return embed


# ============================================================
# RP START
# ============================================================

async def start_rp(
    bot: commands.Bot,
    settings: dict,
    started_by: str,
):
    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        print(
            "❌ RP-Channel nicht gefunden."
        )
        return False

    role = channel.guild.get_role(
        RP_ROLE_ID
    )

    if role is None:
        print(
            "❌ RP-Rolle nicht gefunden."
        )
        return False

    if settings.get(
        "rp_active",
        False,
    ):
        return False

    now = get_german_time()

    embed = discord.Embed(
        title="🟢 EHRP/VC • RP START",
        description=(
            "## ROLEPLAY IST GESTARTET\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Das RP ist jetzt **OFFIZIELL GEÖFFNET**.\n\n"
            "Bitte haltet euch an das Regelwerk "
            "und sorgt für sauberes RP.\n\n"
            f"🕒 **Start:** "
            f"{now.strftime('%H:%M')} Uhr\n"
            f"🇩🇪 **Zeitzone:** Deutschland\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SUCCESS_COLOR,
        timestamp=now,
    )

    embed.set_footer(
        text=(
            f"EHRP | System • Gestartet durch {started_by}"
        )
    )

    try:
        await channel.send(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                roles=True,
                users=False,
                everyone=False,
            ),
        )

    except discord.HTTPException as error:
        print(
            f"❌ RP Start Message Fehler: {error}"
        )
        return False

    settings[
        "rp_active"
    ] = True

    save_settings(
        settings
    )

    return True


# ============================================================
# RP STOP
# ============================================================

async def stop_rp(
    bot: commands.Bot,
    settings: dict,
    stopped_by: str,
):
    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):
        return False

    if not settings.get(
        "rp_active",
        False,
    ):
        return False

    now = get_german_time()

    embed = discord.Embed(
        title="🔴 EHRP/VC • RP STOP",
        description=(
            "## ROLEPLAY BEENDET\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Das offizielle RP wurde beendet.\n\n"
            f"🕒 **Ende:** "
            f"{now.strftime('%H:%M')} Uhr\n"
            f"🇩🇪 **Zeitzone:** Deutschland\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=ERROR_COLOR,
        timestamp=now,
    )

    embed.set_footer(
        text=(
            f"EHRP | System • Beendet durch {stopped_by}"
        )
    )

    try:
        await channel.send(
            embed=embed
        )

    except discord.HTTPException as error:
        print(
            f"❌ RP Stop Message Fehler: {error}"
        )
        return False

    settings[
        "rp_active"
    ] = False

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

        self.auto_rp_loop.start()


    def cog_unload(
        self,
    ):
        self.auto_rp_loop.cancel()


    # ========================================================
    # AUTO LOOP
    # ========================================================

    @tasks.loop(
        seconds=30
    )
    async def auto_rp_loop(
        self,
    ):
        if not self.settings.get(
            "auto_enabled",
            False,
        ):
            return

        now = get_german_time()

        parsed = parse_time(
            self.settings.get(
                "auto_time",
                "18:00",
            )
        )

        if not parsed:
            return

        hour, minute = parsed

        if (
            now.hour != hour
            or now.minute != minute
        ):
            return

        today = now.date().isoformat()

        if (
            self.settings.get(
                "last_auto_date"
            )
            == today
        ):
            return

        success = await start_rp(
            self.bot,
            self.settings,
            "Auto-RP",
        )

        if success:
            self.settings[
                "last_auto_date"
            ] = today

            save_settings(
                self.settings
            )


    @auto_rp_loop.before_loop
    async def before_auto_rp_loop(
        self,
    ):
        await self.bot.wait_until_ready()


    # ========================================================
    # /rp_start
    # ========================================================

    @app_commands.command(
        name="rp_start",
        description=(
            "Startet das RP sofort."
        ),
    )
    async def rp_start(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_rp_owner(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        success = await start_rp(
            self.bot,
            self.settings,
            interaction.user.display_name,
        )

        if success:
            await interaction.followup.send(
                "✅ RP wurde gestartet.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "⚠️ RP läuft bereits oder konnte nicht gestartet werden.",
                ephemeral=True,
            )


    # ========================================================
    # /rp_stop
    # ========================================================

    @app_commands.command(
        name="rp_stop",
        description=(
            "Beendet das laufende RP."
        ),
    )
    async def rp_stop(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_rp_owner(
            interaction
        ):
            return

        await interaction.response.defer(
            ephemeral=True
        )

        success = await stop_rp(
            self.bot,
            self.settings,
            interaction.user.display_name,
        )

        if success:
            await interaction.followup.send(
                "✅ RP wurde beendet.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "⚠️ RP ist bereits offline.",
                ephemeral=True,
            )


    # ========================================================
    # /rp_status
    # ========================================================

    @app_commands.command(
        name="rp_status",
        description=(
            "Zeigt den aktuellen RP-Status."
        ),
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
    # /rp_uhrzeit
    # ========================================================

    @app_commands.command(
        name="rp_uhrzeit",
        description=(
            "Stellt die automatische RP-Startzeit ein."
        ),
    )
    @app_commands.describe(
        uhrzeit=(
            "Deutsche Uhrzeit im Format HH:MM, "
            "z.B. 18:30"
        )
    )
    async def rp_uhrzeit(
        self,
        interaction: discord.Interaction,
        uhrzeit: str,
    ):
        if not await ensure_rp_owner(
            interaction
        ):
            return

        parsed = parse_time(
            uhrzeit
        )

        if not parsed:
            await interaction.response.send_message(
                (
                    "❌ Ungültige Uhrzeit.\n"
                    "Benutze z.B. `/rp_uhrzeit 18:30`."
                ),
                ephemeral=True,
            )
            return

        hour, minute = parsed

        formatted = (
            f"{hour:02d}:{minute:02d}"
        )

        self.settings[
            "auto_time"
        ] = formatted

        self.settings[
            "last_auto_date"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **Auto-RP-Uhrzeit geändert**\n\n"
                f"🕒 Start: **{formatted} Uhr**\n"
                "🇩🇪 Zeitzone: **Deutschland**\n\n"
                f"Auto-RP ist aktuell "
                f"**{'AN' if self.settings['auto_enabled'] else 'AUS'}**."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /rp_auto_an
    # ========================================================

    @app_commands.command(
        name="rp_auto_an",
        description=(
            "Aktiviert den automatischen RP-Start."
        ),
    )
    async def rp_auto_an(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_rp_owner(
            interaction
        ):
            return

        self.settings[
            "auto_enabled"
        ] = True

        self.settings[
            "last_auto_date"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **Auto-RP aktiviert**\n\n"
                f"🕒 Startzeit: "
                f"**{self.settings['auto_time']} Uhr**\n"
                "🇩🇪 Deutsche Zeit"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /rp_auto_aus
    # ========================================================

    @app_commands.command(
        name="rp_auto_aus",
        description=(
            "Deaktiviert den automatischen RP-Start."
        ),
    )
    async def rp_auto_aus(
        self,
        interaction: discord.Interaction,
    ):
        if not await ensure_rp_owner(
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
            "✅ Auto-RP wurde deaktiviert.",
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
