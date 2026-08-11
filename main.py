import os
import discord
from discord.ext import commands


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


bot.run(TOKEN)
