import os

import discord
from discord.ext import commands

from health_server import start_health_server


# ============================================================
# EHRP | SYSTEM — MAIN
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

        print("🔄 Lade EHRP | System Module ...")

        # Recovery
        await self.load_extension(
            "cogs.recovery"
        )
        print("✅ Recovery geladen")

        # Team
        await self.load_extension(
            "cogs.team"
        )
        print("✅ Team-System geladen")

        # Tickets
        await self.load_extension(
            "cogs.tickets"
        )
        print("✅ Ticket-System geladen")

        # RP Control
        await self.load_extension(
            "cogs.rp_control"
        )
        print("✅ RP-Control geladen")

        # Self Roles
        await self.load_extension(
            "cogs.selfroles"
        )
        print("✅ Self-Roles geladen")

        # Team Ideen
        await self.load_extension(
            "cogs.team_ideas"
        )
        print("✅ Team-Ideen geladen")

        # System Dashboard
        await self.load_extension(
            "cogs.system_dashboard"
        )
        print("✅ System Dashboard geladen")

        # Slash Commands synchronisieren
        synced = await self.tree.sync()

        print(
            f"✅ {len(synced)} Slash-Commands synchronisiert"
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

    print("")
    print("========================================")
    print("✅ EHRP | SYSTEM ONLINE")
    print(f"🤖 Bot: {bot.user}")

    if bot.user:
        print(f"🆔 Bot-ID: {bot.user.id}")

    print(f"🌐 Server: {len(bot.guilds)}")
    print("👥 Team-System: ONLINE")
    print("🎫 Ticket-System: ONLINE")
    print("🎮 RP-Control: ONLINE")
    print("🔔 Self-Roles: ONLINE")
    print("💡 Team-Ideen: ONLINE")
    print("⚙️ System Dashboard: ONLINE")
    print("🕐 Alter 13:00 RP-Start: ENTFERNT")
    print("========================================")
    print("")


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

start_health_server()


# ============================================================
# BOT START
# ============================================================

bot.run(TOKEN)
