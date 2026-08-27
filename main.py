import os

import discord
from discord.ext import commands

from health_server import start_health_server


# ============================================================
# EHRP | SYSTEM
# MAIN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN wurde in Render nicht gefunden."
    )


# ============================================================
# DISCORD INTENTS
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

        print("🔄 Lade EHRP | System Module ...")

        # Recovery
        await self.load_extension(
            "cogs.recovery"
        )
        print("✅ Recovery geladen")

        # Team-System
        await self.load_extension(
            "cogs.team"
        )
        print("✅ Team-System geladen")

        # Ticket-System
        await self.load_extension(
            "cogs.tickets"
        )
        print("✅ Ticket-System geladen")

        # RP-Control
        await self.load_extension(
            "cogs.rp_control"
        )
        print("✅ RP-Control geladen")

        # Slash Commands bei Discord registrieren
        synced = await self.tree.sync()

        print(
            f"✅ {len(synced)} Slash-Commands synchronisiert"
        )


bot = EHRPSystem()


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("")
    print("========================================")
    print("✅ EHRP | SYSTEM ONLINE")
    print(f"🤖 Bot: {bot.user}")
    print(
        f"🆔 Bot-ID: "
        f"{bot.user.id if bot.user else 'unbekannt'}"
    )
    print(f"🌐 Server: {len(bot.guilds)}")
    print("🎫 Tickets: ONLINE")
    print("👥 Team-System: ONLINE")
    print("🎮 RP-Control: ONLINE")
    print("🕐 Alter 13:00 RP-Start: ENTFERNT")
    print("========================================")
    print("")


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

start_health_server()


# ============================================================
# START
# ============================================================

bot.run(TOKEN)
