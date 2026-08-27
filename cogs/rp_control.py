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
RP_ROLE_ID = 1526957918128443533

GERMAN_TIMEZONE = ZoneInfo(
    "Europe/Berlin"
)


# ============================================================
# DESIGN
# ============================================================

SYSTEM_COLOR = 0x5865F2
ONLINE_COLOR = 0x57F287
OFFLINE_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C


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


def load_settings() -> dict:

    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()

    try:

        with SETTINGS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:

            loaded = json.load(
                file
            )

        settings = DEFAULT_SETTINGS.copy()

        settings.update(
            loaded
        )

        return settings

    except Exception as error:

        print(
            "❌ RP Einstellungen "
            f"konnten nicht geladen werden: {error}"
        )

        return DEFAULT_SETTINGS.copy()


def save_settings(
    settings: dict,
):

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
            "❌ RP Einstellungen "
            f"konnten nicht gespeichert werden: {error}"
        )


# ============================================================
# TIME
# ============================================================

def german_now() -> datetime:

    return datetime.now(
        GERMAN_TIMEZONE
    )


def parse_clock(
    value: str,
):

    value = value.strip()

    try:

        parsed = datetime.strptime(
            value,
            "%H:%M",
        )

        return (
            parsed.hour,
            parsed.minute,
        )

    except ValueError:

        return None


# ============================================================
# ACCESS
# ============================================================

async def check_control_permission(
    interaction: discord.Interaction,
) -> bool:

    if (
        interaction.user.id
        == CONTROL_USER_ID
    ):
        return True

    await interaction.response.send_message(
        (
            "❌ Du hast keine Berechtigung, "
            "das RP-System zu steuern."
        ),
        ephemeral=True,
    )

    return False


# ============================================================
# STATUS EMBED
# ============================================================

def build_status_embed(
    settings: dict,
):

    now = german_now()

    rp_active = bool(
        settings.get(
            "rp_active",
            False,
        )
    )

    auto_enabled = bool(
        settings.get(
            "auto_enabled",
            False,
        )
    )

    auto_time = settings.get(
        "auto_time",
        "18:00",
    )

    embed = discord.Embed(
        title="🎮 EHRP | RP CONTROL",
        description=(
            "## SYSTEM STATUS\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{'🟢' if rp_active else '🔴'} "
            f"**RP:** "
            f"{'ONLINE' if rp_active else 'OFFLINE'}\n\n"
            f"{'🟢' if auto_enabled else '🔴'} "
            f"**Automatischer Start:** "
            f"{'AN' if auto_enabled else 'AUS'}\n\n"
            f"🕒 **Eingestellte Startzeit:** "
            f"`{auto_time} Uhr`\n\n"
            "🇩🇪 **Zeitzone:** "
            "`Deutschland (Europe/Berlin)`\n\n"
            f"⌚ **Deutsche Uhrzeit jetzt:** "
            f"`{now.strftime('%H:%M:%S')}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=(
            ONLINE_COLOR
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
# START RP
# ============================================================

async def start_roleplay(
    bot: commands.Bot,
    settings: dict,
    started_by: str,
) -> tuple[bool, str]:

    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):

        return (
            False,
            "Der RP-Channel wurde nicht gefunden.",
        )

    role = channel.guild.get_role(
        RP_ROLE_ID
    )

    if role is None:

        return (
            False,
            "Die RP-Rolle wurde nicht gefunden.",
        )

    if settings.get(
        "rp_active",
        False,
    ):

        return (
            False,
            "Das RP läuft bereits.",
        )

    now = german_now()

    embed = discord.Embed(
        title="🟢 EHRP/VC • RP START",
        description=(
            "## ROLEPLAY GESTARTET\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Das offizielle Roleplay ist "
            "**ab sofort geöffnet**. 🎮\n\n"
            "Bitte achtet auf sauberes RP "
            "und haltet euch an das Regelwerk.\n\n"
            f"🕒 **Start:** "
            f"`{now.strftime('%H:%M')} Uhr`\n"
            "🇩🇪 **Zeitzone:** Deutschland\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=ONLINE_COLOR,
        timestamp=now,
    )

    embed.set_footer(
        text=(
            "EHRP | System • "
            f"Gestartet durch {started_by}"
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
            f"❌ RP Start Fehler: {error}"
        )

        return (
            False,
            "Die Start-Nachricht konnte nicht gesendet werden.",
        )

    settings[
        "rp_active"
    ] = True

    save_settings(
        settings
    )

    return (
        True,
        "RP wurde gestartet.",
    )


# ============================================================
# STOP RP
# ============================================================

async def stop_roleplay(
    bot: commands.Bot,
    settings: dict,
    stopped_by: str,
) -> tuple[bool, str]:

    channel = bot.get_channel(
        RP_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):

        return (
            False,
            "Der RP-Channel wurde nicht gefunden.",
        )

    if not settings.get(
        "rp_active",
        False,
    ):

        return (
            False,
            "Das RP ist bereits offline.",
        )

    now = german_now()

    embed = discord.Embed(
        title="🔴 EHRP/VC • RP ENDE",
        description=(
            "## ROLEPLAY BEENDET\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Das offizielle Roleplay "
            "wurde beendet.\n\n"
            f"🕒 **Ende:** "
            f"`{now.strftime('%H:%M')} Uhr`\n"
            "🇩🇪 **Zeitzone:** Deutschland\n\n"
            "Vielen Dank fürs Mitspielen. ❤️\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=OFFLINE_COLOR,
        timestamp=now,
    )

    embed.set_footer(
        text=(
            "EHRP | System • "
            f"Beendet durch {stopped_by}"
        )
    )

    try:

        await channel.send(
            embed=embed
        )

    except discord.HTTPException as error:

        print(
            f"❌ RP Stop Fehler: {error}"
        )

        return (
            False,
            "Die Stop-Nachricht konnte nicht gesendet werden.",
        )

    settings[
        "rp_active"
    ] = False

    save_settings(
        settings
    )

    return (
        True,
        "RP wurde beendet.",
    )


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

        self.settings = (
            load_settings()
        )

        self.auto_start_loop.start()

        print(
            "✅ RP-Control initialisiert"
        )

        print(
            "🕒 Auto-RP: "
            f"{'AN' if self.settings['auto_enabled'] else 'AUS'}"
        )

        print(
            "🕒 Auto-Zeit: "
            f"{self.settings['auto_time']}"
        )


    def cog_unload(
        self,
    ):

        self.auto_start_loop.cancel()


    # ========================================================
    # AUTOMATISCHER CHECK
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

        if self.settings.get(
            "rp_active",
            False,
        ):

            return

        parsed = parse_clock(
            self.settings.get(
                "auto_time",
                "18:00",
            )
        )

        if parsed is None:

            return

        target_hour, target_minute = parsed

        now = german_now()

        if (
            now.hour != target_hour
            or now.minute != target_minute
        ):

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

        success, _ = await start_roleplay(
            self.bot,
            self.settings,
            "Automatik",
        )

        if success:

            self.settings[
                "last_auto_start"
            ] = today

            save_settings(
                self.settings
            )

            print(
                "✅ RP automatisch gestartet "
                f"um {now.strftime('%H:%M')}"
            )


    @auto_start_loop.before_loop
    async def before_auto_start_loop(
        self,
    ):

        await self.bot.wait_until_ready()


    # ========================================================
    # /rp_status
    # ========================================================

    @app_commands.command(
        name="rp_status",
        description=(
            "Zeigt den aktuellen RP-Systemstatus."
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
    # /rp_start
    # ========================================================

    @app_commands.command(
        name="rp_start",
        description=(
            "Startet das RP sofort manuell."
        ),
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

        success, message = (
            await start_roleplay(
                self.bot,
                self.settings,
                interaction.user.display_name,
            )
        )

        if success:

            await interaction.followup.send(
                "✅ **RP wurde gestartet.**",
                ephemeral=True,
            )

        else:

            await interaction.followup.send(
                f"⚠️ {message}",
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

        if not await check_control_permission(
            interaction
        ):

            return

        await interaction.response.defer(
            ephemeral=True
        )

        success, message = (
            await stop_roleplay(
                self.bot,
                self.settings,
                interaction.user.display_name,
            )
        )

        if success:

            await interaction.followup.send(
                "✅ **RP wurde beendet.**",
                ephemeral=True,
            )

        else:

            await interaction.followup.send(
                f"⚠️ {message}",
                ephemeral=True,
            )


    # ========================================================
    # /rp_uhrzeit
    # ========================================================

    @app_commands.command(
        name="rp_uhrzeit",
        description=(
            "Stellt die automatische "
            "RP-Startzeit ein."
        ),
    )
    @app_commands.describe(
        uhrzeit=(
            "Deutsche Uhrzeit, z.B. 18:30"
        )
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
                (
                    "❌ **Ungültige Uhrzeit.**\n\n"
                    "Beispiele:\n"
                    "`18:30`\n"
                    "`19:00`\n"
                    "`21:45`"
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
            "last_auto_start"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **RP-Uhrzeit gespeichert**\n\n"
                f"🕒 **{formatted} Uhr**\n"
                "🇩🇪 Deutsche Zeit\n\n"
                f"Automatik: "
                f"**{'AN' if self.settings['auto_enabled'] else 'AUS'}**"
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

        if not await check_control_permission(
            interaction
        ):

            return

        self.settings[
            "auto_enabled"
        ] = True

        self.settings[
            "last_auto_start"
        ] = None

        save_settings(
            self.settings
        )

        await interaction.response.send_message(
            (
                "✅ **Auto-RP ist jetzt AN**\n\n"
                f"🕒 Start täglich um "
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
            (
                "✅ **Auto-RP ist jetzt AUS**\n\n"
                "Das RP startet nicht mehr automatisch."
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
        RPControl(bot)
    )
