from __future__ import annotations
import asyncio
import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import GUILD_ID
from health_server import start_health_server
from utils.db import init_db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

EXTENSIONS = [
    "cogs.core", "cogs.setup", "cogs.server_scan", "cogs.server_tools",
    "cogs.backup", "cogs.undo", "cogs.templates", "cogs.projects",
    "cogs.voice", "cogs.team", "cogs.embeds", "cogs.logs", "cogs.stats", "cogs.design",
]

class DevBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        intents.message_content = False
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        init_db()
        for ext in EXTENSIONS:
            await self.load_extension(ext)
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        logging.info("Synced %s commands", len(synced))

    async def on_ready(self):
        logging.info("Online as %s (%s)", self.user, self.user.id if self.user else "?")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="EHRP • Development"))

async def main():
    start_health_server()
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN fehlt. Nutze eine .env Datei oder Environment Variable.")
    bot = DevBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
