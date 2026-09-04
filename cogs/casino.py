import discord
from discord import app_commands
from discord.ext import commands


CASINO_URL = "https://dev-ehrp-vc-bot.onrender.com"

CASINO_BANNER_URL = (
    "https://dev-ehrp-vc-bot.onrender.com/"
    "assets/casino_entrance.png.PNG"
)


class CasinoPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="Casino betreten",
                emoji="🎰",
                style=discord.ButtonStyle.link,
                url=CASINO_URL
            )
        )


class Casino(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(
        name="casino",
        description="Öffnet das EHRP/VC Casino."
    )
    async def casino(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="👑 EHRP/VC Casino",
            description=(
                "### Willkommen im EHRP/VC Premium Casino\n\n"
                "Tauche ein in unser exklusives Casino und spiele "
                "mit deinen **EHRP Coins**.\n\n"
                "🎰 **Slots**\n"
                "♠️ **Blackjack**\n"
                "🎡 **Roulette**\n"
                "🪙 **Coinflip**\n"
                "🎲 **Dice**\n"
                "🃏 **Baccarat**\n"
                "♦️ **High / Low**\n"
                "💣 **Mines**\n"
                "🚀 **Crash**\n\n"
                "Dein Discord-Account wird beim Betreten sicher "
                "mit dem Casino verbunden."
            ),
            color=discord.Color.gold()
        )

        embed.set_image(
            url=CASINO_BANNER_URL
        )

        embed.add_field(
            name="💰 EHRP Coins",
            value=(
                "Spiele, sammle Coins und behalte "
                "deine persönlichen Statistiken im Blick."
            ),
            inline=False
        )

        embed.add_field(
            name="🔐 Sicherer Login",
            value=(
                "Kein extra Account nötig — "
                "Login direkt über Discord."
            ),
            inline=False
        )

        embed.set_footer(
            text="EHRP/VC • Premium Casino"
        )

        await interaction.response.send_message(
            embed=embed,
            view=CasinoPanelView()
        )


    @app_commands.command(
        name="casino_panel",
        description="Sendet das öffentliche Casino-Panel."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def casino_panel(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="👑 EHRP/VC Casino",
            description=(
                "## Dein Casino Erlebnis\n\n"
                "Spiele, gewinne und sammle **EHRP Coins**.\n\n"
                "**9 Premium Spiele** warten auf dich.\n\n"
                "Drücke unten auf **Casino betreten** "
                "und starte direkt über deinen Discord-Account."
            ),
            color=discord.Color.gold()
        )

        embed.set_image(
            url=CASINO_BANNER_URL
        )

        embed.add_field(
            name="🎮 9 Spiele",
            value=(
                "Slots • Blackjack • Roulette • Coinflip • Dice • "
                "Baccarat • High / Low • Mines • Crash"
            ),
            inline=False
        )

        embed.add_field(
            name="🏆 Deine Stats",
            value=(
                "Coins, Spiele, Siege, Winrate "
                "und größter Gewinn."
            ),
            inline=True
        )

        embed.add_field(
            name="🔐 Discord Login",
            value=(
                "Sicher verbunden mit deinem Discord-Account."
            ),
            inline=True
        )

        embed.set_footer(
            text="EHRP/VC • More Than A Game"
        )

        await interaction.response.send_message(
            content="✅ Casino-Panel wurde gesendet.",
            ephemeral=True
        )

        await interaction.channel.send(
            embed=embed,
            view=CasinoPanelView()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(
        Casino(bot)
    )
