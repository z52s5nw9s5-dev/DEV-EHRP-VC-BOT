import os
import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from health_server import start_health_server


TOKEN = os.getenv("DISCORD_TOKEN")

RP_CHANNEL_ID = 1529998957449707551
RP_ROLE_ID = 1526957918128443533


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True


# =========================================================
# RP START TEXT
# =========================================================

RP_TEXT = """**EHRP/VC — RP START**

Der RP-Server ist jetzt geöffnet!

Es ist soweit – EHRP/VC startet jetzt offiziell. Alle Einsatzkräfte, Zivilisten und Fraktionen können ab sofort beitreten.

Server beitreten:
Join Code: a3p0jzbe

Direkter Roblox-Join:
https://www.roblox.com/share?code=5b11efb6fa62

Wir erwarten von allen Spielern:
• Realistisches und faires Roleplay
• Einhaltung des Regelwerks
• Respektvollen Umgang miteinander
• Spaß am gemeinsamen RP

Wir freuen uns auf jeden einzelnen von euch und wünschen allen einen erfolgreichen Start auf EHRP/VC.

Das EHRP/VC-Team
"""


# =========================================================
# BOT CLASS
# =========================================================

class EHRPSystemBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        extensions = [
            "cogs.recovery",
            "cogs.team",
            "cogs.tickets",
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ Loaded {extension}")
            except Exception as error:
                print(f"❌ Failed to load {extension}: {error}")
                raise

        synced = await self.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")

        if not daily_rp_start.is_running():
            daily_rp_start.start()

    async def on_ready(self):
        print(
            f"✅ EHRP | System online as "
            f"{self.user} ({self.user.id})"
        )


bot = EHRPSystemBot()


# =========================================================
# DAILY RP START
# =========================================================

@tasks.loop(
    time=datetime.time(
        hour=13,
        minute=0,
        tzinfo=ZoneInfo("Europe/Berlin"),
    )
)
async def daily_rp_start():

    try:
        channel = bot.get_channel(RP_CHANNEL_ID)

        if channel is None:
            try:
                channel = await bot.fetch_channel(RP_CHANNEL_ID)
            except Exception as error:
                print(
                    f"❌ RP channel konnte nicht geladen werden: {error}"
                )
                return

        await channel.send(
            f"<@&{RP_ROLE_ID}>\n\n{RP_TEXT}",
            allowed_mentions=discord.AllowedMentions(
                roles=True,
                users=False,
                everyone=False,
            ),
        )

        print("✅ RP START wurde automatisch gesendet.")

    except Exception as error:
        print(f"❌ RP START Fehler: {error}")


@daily_rp_start.before_loop
async def before_daily_rp_start():
    await bot.wait_until_ready()


# =========================================================
# START
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN wurde in den Environment Variables nicht gefunden."
    )

start_health_server()

bot.run(TOKEN)
