import asyncio
import os

import discord
from discord.ext import commands

from health_server import keep_alive


# ============================================================
# BOT CONFIG
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
intents.message_content = True
intents.messages = True


# ============================================================
# BOT
# ============================================================

class EHRPBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )


    async def setup_hook(self):

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🚀 EHRP | System startet …")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


        # ====================================================
        # COGS
        # ====================================================

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
                    f"❌ Fehler beim Laden von {extension}"
                )

                print(
                    f"   {type(error).__name__}: {error}"
                )


        # ====================================================
        # SLASH COMMAND SYNC
        # ====================================================

        try:

            synced = await self.tree.sync()

            print(
                f"✅ Slash Commands synchronisiert: {len(synced)}"
            )

            for command in synced:

                print(
                    f"   /{command.name}"
                )

        except Exception as error:

            print(
                "❌ Slash Commands konnten nicht "
                "synchronisiert werden:"
            )

            print(
                f"   {type(error).__name__}: {error}"
            )


        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ Setup abgeschlossen")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


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
        # STATUS
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


    async def on_error(
        self,
        event_method,
        *args,
        **kwargs,
    ):

        print(
            f"❌ Unbehandelter Fehler bei Event: {event_method}"
        )


# ============================================================
# START BOT
# ============================================================

bot = EHRPBot()


async def main():

    # Render Health Server
    keep_alive()

    try:

        async with bot:

            await bot.start(
                TOKEN
            )

    except discord.LoginFailure:

        print(
            "❌ Discord Login fehlgeschlagen."
        )

        print(
            "Bitte DISCORD_TOKEN auf Render prüfen."
        )

    except KeyboardInterrupt:

        print(
            "🛑 Bot wurde gestoppt."
        )

    except Exception as error:

        print(
            "❌ Kritischer Bot-Fehler:"
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
