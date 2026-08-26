import os
import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from health_server import start_health_server

TOKEN = os.getenv("DISCORD_TOKEN")

RP_CHANNEL_ID = 1529998957449707551
RP_ROLE_ID = 1526957918128443533

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

RP_TEXT = """**EHRP/VC – RP START**
Der RP-Server ist jetzt geöffnet!

Es ist soweit – EHRP/VC startet jetzt offiziell. Alle Einsatzkräfte, Zivilisten und Fraktionen können ab sofort beitreten und gemeinsam realistisches sowie hochwertiges Roleplay erleben.

Server beitreten:
Join Code: a3pu7mbc

Direkter Roblox-Join:
https://www.roblox.com/share?v=v2&code=5ihdm3h6q1r232

Wir erwarten von allen Spielern:
Realistisches und faires Roleplay
Einhaltung des Regelwerks
Respektvollen Umgang miteinander
Spaß am gemeinsamen RP

Wir freuen uns auf jeden einzelnen von euch und wünschen allen einen erfolgreichen Start auf EHRP/VC.

Das EHRP/VC-Team"""


class RecoveryBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
    await self.load_extension("cogs.recovery")
    await self.load_extension("cogs.team")
    await self.load_extension("cogs.tickets")

    synced = await self.tree.sync()
    print(f"✅ Synced {len(synced)} command(s)")

    if not daily_rp_start.is_running():
        daily_rp_start.start()

bot = RecoveryBot()


@tasks.loop(
    time=datetime.time(
        hour=13,
        minute=0,
        tzinfo=ZoneInfo("Europe/Berlin")
    )
)
async def daily_rp_start():
    try:
        channel = await bot.fetch_channel(RP_CHANNEL_ID)

        await channel.send(
            f"<@&{RP_ROLE_ID}>\n\n{RP_TEXT}",
            allowed_mentions=discord.AllowedMentions(
                roles=True,
                users=False,
                everyone=False
            )
        )

        print("✅ RP START wurde automatisch gesendet.")

    except Exception as error:
        print(f"❌ RP START Fehler: {error}")


@daily_rp_start.before_loop
async def before_daily_rp_start():
    await bot.wait_until_ready()


start_health_server()
bot.run(TOKEN)
