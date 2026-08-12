import os
import discord
from discord.ext import commands
from health_server import start_health_server

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True


class RecoveryBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        # NUR Recovery laden
        await self.load_extension("cogs.recovery")

        # NUR einmal synchronisieren
        synced = await self.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")


bot = RecoveryBot()


@bot.event
async def on_ready():
    print(f"✅ Online als {bot.user}")

import os
import discord
from discord.ext import commands, tasks
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("DISCORD_TOKEN")

TEST_GUILD_ID = 1530332131421589584
TEST_CHANNEL_ID = 1532399275206770799

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

sent = False

RP_TEXT = """**EHRP/VC – RP START**

Der RP-Server ist jetzt geöffnet!

Es ist soweit – EHRP/VC startet jetzt offiziell. Alle Einsatzkräfte, Zivilisten und Fraktionen können ab sofort beitreten und gemeinsam realistisches sowie hochwertiges Roleplay erleben.

**Server beitreten:**
Join Code: `a3pu7mbc`

**Direkter Roblox-Join:**
https://www.roblox.com/share?v=v2&code=5ihdm3h6q1r232

**Wir erwarten von allen Spielern:**
• Realistisches und faires Roleplay
• Einhaltung des Regelwerks
• Respektvollen Umgang miteinander
• Spaß am gemeinsamen RP

Wir freuen uns auf jeden einzelnen von euch und wünschen allen einen erfolgreichen Start auf EHRP/VC.

Das EHRP/VC-Team

test
"""

@bot.event
async def on_ready():
    print(f"{bot.user} ist online")
    if not rp_test.is_running():
        rp_test.start()

@tasks.loop(seconds=10)
async def rp_test():
    global sent

    now = datetime.now(ZoneInfo("Europe/Berlin"))

    if (
        not sent
        and now.year == 2026
        and now.month == 8
        and now.day == 12
        and now.hour == 13
        and now.minute == 0
    ):
        channel = bot.get_channel(TEST_CHANNEL_ID)

        if channel:
            await channel.send(RP_TEXT)
            sent = True
            print("RP-Start Test wurde gesendet.")


start_health_server()
bot.run(TOKEN)
