import asyncio
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
intents.messages = True
intents.message_content = True


# ============================================================
# BOT
# ============================================================

class EHRPBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
        )


    # ========================================================
    # SETUP
    # ========================================================

    async def setup_hook(self):

        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🚀 EHRP | SYSTEM STARTET")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


        extensions = [
            "cogs.recovery",
            "cogs.team",
            "cogs.tickets",
            "cogs.rp_control",
            "cogs.selfroles",
            "cogs.team_ideas",
            "cogs.system_dashboard",
            "cogs.applications",
        ]


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
                    f"❌ Fehler bei: {extension}"
                )

                print(
                    f"   {type(error).__name__}: {error}"
                )


        # ====================================================
        # SLASH COMMANDS
        # ====================================================

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
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ SETUP ABGESCHLOSSEN")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


    # ========================================================
    # READY
    # ========================================================

    async def on_ready(self):

        if self.user is None:
            return


        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🟢 EHRP | SYSTEM ONLINE")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(
            f"🤖 Bot: {self.user}"
        )
        print(
            f"🆔 Bot-ID: {self.user.id}"
        )
        print(
            f"🌐 Server: {len(self.guilds)}"
        )
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


        # ====================================================
        # BOT STATUS
        # ====================================================

        try:

            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="EHRP/VC",
            )

            await self.change_presence(
                status=discord.Status.online,
                activity=activity,
            )

        except Exception as error:

            print(
                f"⚠️ Status konnte nicht gesetzt werden: {error}"
            )


    # ========================================================
    # GLOBAL EVENT ERROR
    # ========================================================

    async def on_error(
        self,
        event_method,
        *args,
        **kwargs,
    ):

        print(
            f"❌ Fehler bei Discord Event: {event_method}"
        )


# ============================================================
# CREATE BOT
# ============================================================

bot = EHRPBot()


# ============================================================
# MAIN
# ============================================================

async def main():

    # Render Health Server starten
    start_health_server()

    print(
        "🟢 Health Server gestartet."
    )


    try:

        async with bot:

            await bot.start(
                TOKEN
            )


    except discord.LoginFailure:

        print("")
        print("❌ Discord Login fehlgeschlagen.")
        print(
            "Prüfe DISCORD_TOKEN in den Render Environment Variables."
        )


    except KeyboardInterrupt:

        print(
            "🛑 Bot wurde beendet."
        )


    except Exception as error:

        print("")
        print(
            "❌ KRITISCHER BOT-FEHLER"
        )

        print(
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
