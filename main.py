import asyncio
import os
import threading

import discord
from discord.ext import commands

from app import app


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN wurde nicht gefunden.")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.guild_messages = True

# Wichtig für Bewerbungs-DMs
intents.dm_messages = True
intents.message_content = True


# =========================================================
# WEB CASINO
# =========================================================

def start_web_casino():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    print("")
    print("======================================")
    print("🎰 EHRP/VC WEB CASINO START")
    print(f"🌐 PORT: {port}")
    print("======================================")
    print("")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# BOT
# =========================================================

class EHRPBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents
        )


    async def setup_hook(self):

        extensions = [
            "cogs.recovery",
            "cogs.team",
            "cogs.tickets",
            "cogs.rp_control",
            "cogs.selfroles",
            "cogs.team_ideas",
            "cogs.system_dashboard",
            "cogs.applications",
            "cogs.casino",
        ]

        print("")
        print("======================================")
        print("🚀 EHRP/VC SYSTEM START")
        print("======================================")
        print("")

        for extension in extensions:

            try:

                await self.load_extension(
                    extension
                )

                print(
                    f"✅ Geladen: {extension}"
                )

            except Exception as error:

                print(
                    f"❌ Fehler beim Laden: {extension}"
                )

                print(
                    f"   {type(error).__name__}: {error}"
                )

        print("")
        print("--------------------------------------")
        print(
            "🔄 Slash Commands werden synchronisiert..."
        )
        print("--------------------------------------")

        try:

            synced = await self.tree.sync()

            print("")
            print(
                f"✅ Slash Commands synchronisiert: {len(synced)}"
            )

            for command in synced:

                print(
                    f"   /{command.name}"
                )

        except Exception as error:

            print("")
            print(
                "❌ Slash Commands konnten nicht synchronisiert werden."
            )

            print(
                f"{type(error).__name__}: {error}"
            )

        print("")
        print("======================================")
        print("✅ SETUP ABGESCHLOSSEN")
        print("======================================")
        print("")


    async def on_ready(self):

        if self.user is None:
            return

        print("")
        print("======================================")
        print(
            "🟢 EHRP | SYSTEM ONLINE"
        )
        print(
            f"🤖 Bot: {self.user}"
        )
        print(
            f"🆔 ID: {self.user.id}"
        )
        print(
            f"🌐 Server: {len(self.guilds)}"
        )
        print("======================================")
        print("")

        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="EHRP/VC Casino"
            ),
        )


# =========================================================
# BOT INSTANCE
# =========================================================

bot = EHRPBot()


# =========================================================
# MAIN
# =========================================================

async def main():

    # Web-Casino im Hintergrund starten
    web_thread = threading.Thread(
        target=start_web_casino,
        daemon=True
    )

    web_thread.start()

    # Discord Bot starten
    async with bot:

        await bot.start(
            TOKEN
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
