import os

import discord
from discord.ext import commands

from health_server import start_health_server


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

class EHRPSystem(
    commands.Bot
):
    def __init__(
        self,
    ):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )


    async def setup_hook(
        self,
    ):
        print(
            "🔄 Lade EHRP | System ..."
        )

        await self.load_extension(
            "cogs.recovery"
        )
        print("✅ Recovery")

        await self.load_extension(
            "cogs.team"
        )
        print("✅ Team")

        await self.load_extension(
            "cogs.tickets"
        )
        print("✅ Tickets")

        await self.load_extension(
            "cogs.rp_control"
        )
        print("✅ RP-Control")

        await self.load_extension(
            "cogs.selfroles"
        )
        print("✅ Self-Roles")

        await self.load_extension(
            "cogs.system_dashboard"
        )
        print("✅ System Dashboard")

        synced = await self.tree.sync()

        print(
            f"✅ {len(synced)} "
            "Slash-Commands synchronisiert"
        )


bot = EHRPSystem()


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready(
):
    print("")
    print("========================================")
    print("✅ EHRP | SYSTEM ONLINE")
    print(f"🤖 Bot: {bot.user}")
    print(f"🌐 Server: {len(bot.guilds)}")
    print("👥 Team: ONLINE")
    print("🎫 Tickets: ONLINE")
    print("🎮 RP-Control: ONLINE")
    print("🔔 Self-Roles: ONLINE")
    print("⚙️ Control Center: ONLINE")
    print("🕐 Fester 13-Uhr-Start: ENTFERNT")
    print("========================================")
    print("")


# ============================================================
# RENDER
# ============================================================

start_health_server()


# ============================================================
# START
# ============================================================

bot.run(
    TOKEN
)
