import os

import discord
from discord.ext import commands

from health_server import start_health_server


# ============================================================
# TOKEN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN wurde nicht gefunden."
    )


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True


# ============================================================
# BOT
# ============================================================

class EHRPSystem(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):

        # --------------------------------------------
        # COGS LADEN
        # --------------------------------------------

        await self.load_extension(
            "cogs.recovery"
        )

        await self.load_extension(
            "cogs.team"
        )

        await self.load_extension(
            "cogs.tickets"
        )

        # RP-Control kommt danach hier dazu:
        #
        # await self.load_extension(
        #     "cogs.rp_control"
        # )

        # --------------------------------------------
        # SLASH COMMANDS
        # --------------------------------------------

        synced = await self.tree.sync()

        print(
            f"✅ {len(synced)} Slash-Commands synchronisiert."
        )


# ============================================================
# BOT INSTANZ
# ============================================================

bot = EHRPSystem()


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"✅ EHRP | System ONLINE"
    )

    print(
        f"🤖 Eingeloggt als: {bot.user}"
    )

    print(
        f"🆔 Bot-ID: {bot.user.id if bot.user else 'Unbekannt'}"
    )

    print(
        f"🌐 Server: {len(bot.guilds)}"
    )

    print(
        "🕒 Alter 13-Uhr-RP-Start: DEAKTIVIERT"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


# ============================================================
# HEALTH SERVER
# ============================================================

start_health_server()


# ============================================================
# START
# ============================================================

bot.run(TOKEN)
