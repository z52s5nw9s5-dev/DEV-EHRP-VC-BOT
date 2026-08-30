import asyncio
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

# =========================================================
# EHRP/VC CASINO
# Rein virtuelle Spielwährung – kein Echtgeld.
# =========================================================

START_BALANCE = 1_000
DAILY_REWARD = 250
BET_OPTIONS = [50, 100, 250, 500]
CASINO_COLOR = 0xD4AF37

# Optional: Setze auf Render CASINO_DATA_DIR=/var/data, wenn du einen
# Persistent Disk nach /var/data gemountet hast. Sonst wird lokal gespeichert.
DATA_DIR = Path(os.getenv("CASINO_DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "casino_data.json"

# Intro-Datei im Repo:
CASINO_INTRO = Path("assets/ehrp_casino_intro.gif")

# Optionaler Log-Channel. 0 = deaktiviert.
CASINO_LOG_CHANNEL_ID = int(os.getenv("CASINO_LOG_CHANNEL_ID", "0"))

# Admin / Owner kann das Panel posten und Coins verwalten.
OWNER_USER_ID = 1294267376459714621

# Schutz gegen Spam / Doppel-Klicks
USER_LOCKS: dict[int, asyncio.Lock] = {}


# =========================================================
# STORAGE
# =========================================================

def _ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")


def load_data() -> dict:
    _ensure_storage()
    try:
        raw = DATA_FILE.read_text(encoding="utf-8").strip()
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def save_data(data: dict):
    _ensure_storage()
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(DATA_FILE)


casino_data = load_data()


def default_player() -> dict:
    return {
        "balance": START_BALANCE,
        "daily": None,
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "total_won": 0,
        "total_lost": 0,
        "biggest_win": 0,
    }


def get_player(user_id: int) -> dict:
    uid = str(user_id)
    if uid not in casino_data:
        casino_data[uid] = default_player()
        save_data(casino_data)
    else:
        # Neue Felder nach Updates automatisch ergänzen.
        template = default_player()
        changed = False
        for key, value in template.items():
            if key not in casino_data[uid]:
                casino_data[uid][key] = value
                changed = True
        if changed:
            save_data(casino_data)
    return casino_data[uid]


def get_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_LOCKS:
        USER_LOCKS[user_id] = asyncio.Lock()
    return USER_LOCKS[user_id]


def fmt(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


# =========================================================
# EMBEDS / LOGS
# =========================================================

def casino_embed(
    title: str,
    description: str,
    user: discord.abc.User | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=CASINO_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    if user is not None:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.set_footer(text="EHRP/VC • Casino • Nur virtuelle Spielwährung")
    return embed


async def casino_log(
    guild: discord.Guild | None,
    title: str,
    description: str,
):
    if guild is None or not CASINO_LOG_CHANNEL_ID:
        return
    channel = guild.get_channel(CASINO_LOG_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(embed=casino_embed(title, description))
    except discord.HTTPException:
        pass


async def respond_ephemeral(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
):
    if interaction.response.is_done():
        await interaction.followup.send(
            content=content,
            embed=embed,
            view=view,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            content=content,
            embed=embed,
            view=view,
            ephemeral=True,
        )


async def not_enough(interaction: discord.Interaction, bet: int):
    player = get_player(interaction.user.id)
    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "💳 Nicht genügend EHRP Coins",
            (
                f"Für diesen Einsatz benötigen Sie **{fmt(bet)} Coins**.\n\n"
                f"💰 Ihr Guthaben: **{fmt(player['balance'])} Coins**"
            ),
            interaction.user,
        ),
    )


def is_casino_admin(interaction: discord.Interaction) -> bool:
    if interaction.user.id == OWNER_USER_ID:
        return True
    if isinstance(interaction.user, discord.Member):
        return interaction.user.guild_permissions.administrator
    return False


# =========================================================
# BET SELECT
# Der Einsatz wird pro Nutzer in der View gespeichert.
# =========================================================

class BetSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="💰 Einsatz auswählen",
            min_values=1,
            max_values=1,
            custom_id="ehrp_casino:bet",
            options=[
                discord.SelectOption(
                    label=f"{fmt(bet)} EHRP Coins",
                    value=str(bet),
                    emoji="💰",
                )
                for bet in BET_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, CasinoMainView):
            return
        self.view.user_bets[interaction.user.id] = int(self.values[0])
        await respond_ephemeral(
            interaction,
            content=f"✅ Ihr Einsatz wurde auf **{fmt(int(self.values[0]))} EHRP Coins** gesetzt.",
        )


# =========================================================
# SLOT MACHINE
# =========================================================

SLOT_SYMBOLS = ["🍒", "🍋", "🔔", "BAR", "👑", "💎", "7️⃣"]


def slot_multiplier(result: list[str]) -> float:
    a, b, c = result

    if a == b == c:
        return {
            "7️⃣": 12.0,
            "💎": 10.0,
            "👑": 7.0,
            "BAR": 5.0,
            "🔔": 4.0,
            "🍒": 3.5,
            "🍋": 3.0,
        }.get(a, 3.0)

    if a == b or b == c or a == c:
        return 1.5

    return 0.0


# =========================================================
# COINFLIP
# =========================================================

class CoinflipView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

    async def resolve(self, interaction: discord.Interaction, choice: str):
        if interaction.user.id != self.owner_id:
            return await respond_ephemeral(
                interaction,
                content="❌ Dieses Spiel gehört nicht Ihnen.",
            )

        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde wurde bereits beendet.",
            )

        async with get_lock(interaction.user.id):
            player = get_player(interaction.user.id)

            if player["balance"] < self.bet:
                return await not_enough(interaction, self.bet)

            self.finished = True
            result = random.choice(["Kopf", "Zahl"])
            player["games"] += 1

            if choice == result:
                profit = self.bet
                player["balance"] += profit
                player["wins"] += 1
                player["total_won"] += profit
                player["biggest_win"] = max(player["biggest_win"], profit)
                status = f"✅ **Gewonnen!**\n\nGewinn: **+{fmt(profit)} Coins**"
            else:
                player["balance"] -= self.bet
                player["losses"] += 1
                player["total_lost"] += self.bet
                status = f"❌ **Verloren.**\n\nVerlust: **-{fmt(self.bet)} Coins**"

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        embed = casino_embed(
            "🪙 EHRP Coinflip",
            (
                f"# {result}\n\n"
                f"Ihre Wahl: **{choice}**\n\n"
                f"{status}\n\n"
                f"💰 Guthaben: **{fmt(player['balance'])} Coins**"
            ),
            interaction.user,
        )

        await interaction.response.edit_message(embed=embed, view=self)
        await casino_log(
            interaction.guild,
            "🪙 Coinflip",
            f"{interaction.user.mention} • Einsatz **{fmt(self.bet)}** • Ergebnis **{result}**",
        )

    @discord.ui.button(label="Kopf", emoji="👑", style=discord.ButtonStyle.secondary)
    async def heads(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "Kopf")

    @discord.ui.button(label="Zahl", emoji="🪙", style=discord.ButtonStyle.secondary)
    async def tails(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "Zahl")


# =========================================================
# BLACKJACK
# =========================================================

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def new_deck() -> list[str]:
    deck = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck


def card_rank(card: str) -> str:
    return card[:-1]


def hand_value(hand: list[str]) -> int:
    total = 0
    aces = 0
    for card in hand:
        rank = card_rank(card)
        if rank in ("J", "Q", "K"):
            total += 10
        elif rank == "A":
            total += 11
            aces += 1
        else:
            total += int(rank)

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def hand_text(hand: list[str], hide_second: bool = False) -> str:
    if hide_second and len(hand) > 1:
        return f"`{hand[0]}` `??`"
    return " ".join(f"`{card}`" for card in hand)


class BlackjackView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.bet = bet
        self.deck = new_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.finished = False

    def game_embed(self, user: discord.abc.User, reveal_dealer: bool = False, result: str | None = None):
        pval = hand_value(self.player_hand)
        dval = hand_value(self.dealer_hand)

        dealer_value = str(dval) if reveal_dealer else str(hand_value([self.dealer_hand[0]]))
        description = (
            f"### Ihre Karten\n"
            f"{hand_text(self.player_hand)}\n"
            f"**Wert: {pval}**\n\n"
            f"### Dealer\n"
            f"{hand_text(self.dealer_hand, hide_second=not reveal_dealer)}\n"
            f"**Wert: {dealer_value}**\n\n"
            f"💰 Einsatz: **{fmt(self.bet)} Coins**"
        )

        if result:
            description += f"\n\n━━━━━━━━━━━━━━━━━━\n\n{result}"

        return casino_embed("🃏 EHRP Blackjack", description, user)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(interaction, content="❌ Dieses Blackjack-Spiel gehört nicht Ihnen.")
            return False
        return True

    async def finish(self, interaction: discord.Interaction, outcome: str):
        if self.finished:
            return

        self.finished = True
        player = get_player(self.owner_id)
        player["games"] += 1

        if outcome == "blackjack":
            profit = int(self.bet * 1.5)
            player["balance"] += profit
            player["wins"] += 1
            player["total_won"] += profit
            player["biggest_win"] = max(player["biggest_win"], profit)
            result = f"✨ **BLACKJACK!**\nGewinn: **+{fmt(profit)} Coins**"

        elif outcome == "win":
            profit = self.bet
            player["balance"] += profit
            player["wins"] += 1
            player["total_won"] += profit
            player["biggest_win"] = max(player["biggest_win"], profit)
            result = f"✅ **Sie gewinnen.**\nGewinn: **+{fmt(profit)} Coins**"

        elif outcome == "draw":
            player["draws"] += 1
            result = "⚖️ **Push / Unentschieden.**\nDer Einsatz bleibt erhalten."

        else:
            player["balance"] -= self.bet
            player["losses"] += 1
            player["total_lost"] += self.bet
            result = f"❌ **Dealer gewinnt.**\nVerlust: **-{fmt(self.bet)} Coins**"

        save_data(casino_data)

        for item in self.children:
            item.disabled = True

        result += f"\n\n💰 Guthaben: **{fmt(player['balance'])} Coins**"

        await interaction.response.edit_message(
            embed=self.game_embed(interaction.user, reveal_dealer=True, result=result),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "🃏 Blackjack",
            f"{interaction.user.mention} • Einsatz **{fmt(self.bet)}** • Ergebnis **{outcome}**",
        )

    @discord.ui.button(label="Hit", emoji="➕", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finished:
            return

        self.player_hand.append(self.deck.pop())
        value = hand_value(self.player_hand)

        if value > 21:
            return await self.finish(interaction, "lose")

        if value == 21:
            return await self.stand_logic(interaction)

        await interaction.response.edit_message(
            embed=self.game_embed(interaction.user),
            view=self,
        )

    @discord.ui.button(label="Stand", emoji="✋", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.stand_logic(interaction)

    async def stand_logic(self, interaction: discord.Interaction):
        if self.finished:
            return

        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

        pval = hand_value(self.player_hand)
        dval = hand_value(self.dealer_hand)

        if dval > 21 or pval > dval:
            outcome = "win"
        elif pval < dval:
            outcome = "lose"
        else:
            outcome = "draw"

        await self.finish(interaction, outcome)


# =========================================================
# LEADERBOARD
# =========================================================

def leaderboard_embed(guild: discord.Guild) -> discord.Embed:
    ranking = sorted(
        casino_data.items(),
        key=lambda item: int(item[1].get("balance", 0)),
        reverse=True,
    )[:10]

    if not ranking:
        text = "Noch keine Casino-Spieler vorhanden."
    else:
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for index, (uid, pdata) in enumerate(ranking, start=1):
            member = guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"
            prefix = medals[index - 1] if index <= 3 else f"`#{index}`"
            lines.append(
                f"{prefix} **{name}** — **{fmt(pdata.get('balance', 0))} Coins**"
            )
        text = "\n".join(lines)

    return casino_embed(
        "🏆 EHRP Casino • Top 10",
        text,
    )


# =========================================================
# MAIN CASINO PANEL
# =========================================================

class CasinoMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.user_bets: dict[int, int] = {}
        self.add_item(BetSelect())

    def bet_for(self, user_id: int) -> int:
        return self.user_bets.get(user_id, 100)

    @discord.ui.button(
        label="Kontostand",
        emoji="💰",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp_casino:balance",
        row=1,
    )
    async def balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = get_player(interaction.user.id)
        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "💰 Ihr Casino-Konto",
                (
                    f"# {fmt(p['balance'])} EHRP Coins\n\n"
                    f"🎮 Spiele: **{fmt(p['games'])}**\n"
                    f"✅ Siege: **{fmt(p['wins'])}**\n"
                    f"❌ Niederlagen: **{fmt(p['losses'])}**\n"
                    f"⚖️ Unentschieden: **{fmt(p['draws'])}**\n\n"
                    f"📈 Gesamt gewonnen: **{fmt(p['total_won'])}**\n"
                    f"📉 Gesamt verloren: **{fmt(p['total_lost'])}**\n"
                    f"💎 Größter Gewinn: **{fmt(p['biggest_win'])}**"
                ),
                interaction.user,
            ),
        )

    @discord.ui.button(
        label="Daily",
        emoji="🎁",
        style=discord.ButtonStyle.success,
        custom_id="ehrp_casino:daily",
        row=1,
    )
    async def daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with get_lock(interaction.user.id):
            p = get_player(interaction.user.id)
            now = datetime.now(timezone.utc)
            last_raw = p.get("daily")

            if last_raw:
                try:
                    last = datetime.fromisoformat(last_raw)
                    next_daily = last + timedelta(hours=24)
                    if now < next_daily:
                        remaining = next_daily - now
                        total_minutes = max(1, int(remaining.total_seconds() // 60))
                        hours, minutes = divmod(total_minutes, 60)
                        return await respond_ephemeral(
                            interaction,
                            embed=casino_embed(
                                "⏳ Daily Bonus",
                                f"Bereits abgeholt.\n\n⏱️ Wieder verfügbar in **{hours} Std. {minutes} Min.**",
                                interaction.user,
                            ),
                        )
                except ValueError:
                    pass

            p["balance"] += DAILY_REWARD
            p["daily"] = now.isoformat()
            save_data(casino_data)

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🎁 Daily Bonus",
                (
                    f"**+{fmt(DAILY_REWARD)} EHRP Coins** gutgeschrieben.\n\n"
                    f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
        )

    @discord.ui.button(
        label="Slots",
        emoji="🎰",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp_casino:slots",
        row=2,
    )
    async def slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        bet = self.bet_for(interaction.user.id)

        async with get_lock(interaction.user.id):
            p = get_player(interaction.user.id)
            if p["balance"] < bet:
                return await not_enough(interaction, bet)

            result = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
            mult = slot_multiplier(result)
            p["games"] += 1

            if mult > 0:
                payout = int(bet * mult)
                profit = payout - bet

                # Einsatz ist konzeptionell in der Auszahlung enthalten:
                # Kontostand verändert sich nur um den Nettogewinn.
                p["balance"] += profit
                p["wins"] += 1
                if profit > 0:
                    p["total_won"] += profit
                    p["biggest_win"] = max(p["biggest_win"], profit)

                status = (
                    f"✨ **GEWINN**\n"
                    f"Multiplikator: **x{mult:g}**\n"
                    f"Auszahlung: **{fmt(payout)} Coins**\n"
                    f"Nettogewinn: **+{fmt(profit)} Coins**"
                )
            else:
                p["balance"] -= bet
                p["losses"] += 1
                p["total_lost"] += bet
                status = f"❌ **Kein Gewinn**\nVerlust: **-{fmt(bet)} Coins**"

            save_data(casino_data)

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🎰 EHRP Slots",
                (
                    f"# ┃ {result[0]} ┃ {result[1]} ┃ {result[2]} ┃\n\n"
                    f"{status}\n\n"
                    f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
        )
        await casino_log(
            interaction.guild,
            "🎰 Slots",
            f"{interaction.user.mention} • Einsatz **{fmt(bet)}** • {' | '.join(result)}",
        )

    @discord.ui.button(
        label="Blackjack",
        emoji="🃏",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp_casino:blackjack",
        row=2,
    )
    async def blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        bet = self.bet_for(interaction.user.id)
        p = get_player(interaction.user.id)

        if p["balance"] < bet:
            return await not_enough(interaction, bet)

        view = BlackjackView(interaction.user.id, bet)

        # Natural Blackjack direkt auswerten.
        if hand_value(view.player_hand) == 21:
            if hand_value(view.dealer_hand) == 21:
                await interaction.response.send_message(
                    embed=view.game_embed(interaction.user, reveal_dealer=True),
                    view=view,
                    ephemeral=True,
                )
                # Nachricht danach per Button-Logik sauber finalisieren ist hier nicht nötig;
                # wir rechnen sofort.
                msg_interaction = interaction
                # response ist schon erfolgt, daher separate Verarbeitung:
                view.finished = True
                p["games"] += 1
                p["draws"] += 1
                save_data(casino_data)
                for item in view.children:
                    item.disabled = True
                await interaction.edit_original_response(
                    embed=view.game_embed(
                        interaction.user,
                        reveal_dealer=True,
                        result=f"⚖️ **Beide haben Blackjack. Push.**\n\n💰 Guthaben: **{fmt(p['balance'])} Coins**",
                    ),
                    view=view,
                )
                return
            else:
                await interaction.response.send_message(
                    embed=view.game_embed(interaction.user, reveal_dealer=True),
                    view=view,
                    ephemeral=True,
                )
                view.finished = True
                profit = int(bet * 1.5)
                p["games"] += 1
                p["wins"] += 1
                p["balance"] += profit
                p["total_won"] += profit
                p["biggest_win"] = max(p["biggest_win"], profit)
                save_data(casino_data)
                for item in view.children:
                    item.disabled = True
                await interaction.edit_original_response(
                    embed=view.game_embed(
                        interaction.user,
                        reveal_dealer=True,
                        result=f"✨ **BLACKJACK!**\nGewinn: **+{fmt(profit)} Coins**\n\n💰 Guthaben: **{fmt(p['balance'])} Coins**",
                    ),
                    view=view,
                )
                return

        await interaction.response.send_message(
            embed=view.game_embed(interaction.user),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Coinflip",
        emoji="🪙",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp_casino:coinflip",
        row=2,
    )
    async def coinflip(self, interaction: discord.Interaction, button: discord.ui.Button):
        bet = self.bet_for(interaction.user.id)
        p = get_player(interaction.user.id)

        if p["balance"] < bet:
            return await not_enough(interaction, bet)

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🪙 EHRP Coinflip",
                f"Einsatz: **{fmt(bet)} EHRP Coins**\n\nWählen Sie **Kopf** oder **Zahl**.",
                interaction.user,
            ),
            view=CoinflipView(interaction.user.id, bet),
        )

    @discord.ui.button(
        label="Dice",
        emoji="🎲",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp_casino:dice",
        row=3,
    )
    async def dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        bet = self.bet_for(interaction.user.id)

        async with get_lock(interaction.user.id):
            p = get_player(interaction.user.id)
            if p["balance"] < bet:
                return await not_enough(interaction, bet)

            user_roll = random.randint(1, 6)
            casino_roll = random.randint(1, 6)
            p["games"] += 1

            if user_roll > casino_roll:
                p["balance"] += bet
                p["wins"] += 1
                p["total_won"] += bet
                p["biggest_win"] = max(p["biggest_win"], bet)
                status = f"✅ **Sie gewinnen!**\n+**{fmt(bet)} Coins**"
            elif user_roll < casino_roll:
                p["balance"] -= bet
                p["losses"] += 1
                p["total_lost"] += bet
                status = f"❌ **Casino gewinnt.**\n-**{fmt(bet)} Coins**"
            else:
                p["draws"] += 1
                status = "⚖️ **Unentschieden.**\nKein Verlust."

            save_data(casino_data)

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🎲 EHRP Dice",
                (
                    f"### Sie\n# 🎲 {user_roll}\n\n"
                    f"### Casino\n# 🎲 {casino_roll}\n\n"
                    f"{status}\n\n"
                    f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
        )
        await casino_log(
            interaction.guild,
            "🎲 Dice",
            f"{interaction.user.mention} • **{user_roll} : {casino_roll}** • Einsatz **{fmt(bet)}**",
        )

    @discord.ui.button(
        label="Leaderboard",
        emoji="🏆",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp_casino:leaderboard",
        row=3,
    )
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return await respond_ephemeral(interaction, content="❌ Nur auf dem Server verfügbar.")
        await respond_ephemeral(
            interaction,
            embed=leaderboard_embed(interaction.guild),
        )


# =========================================================
# PANEL
# =========================================================

def main_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎰 EHRP/VC • CASINO",
        description=(
            "## Willkommen im EHRP Casino\n"
            "Luxus, Risiko und Glück – direkt auf dem EHRP/VC Discord.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎰 **Slots** — klassische Walzen & Multiplikatoren\n"
            "🃏 **Blackjack** — Hit / Stand gegen den Dealer\n"
            "🪙 **Coinflip** — Kopf oder Zahl\n"
            "🎲 **Dice** — Ihr Würfel gegen das Casino\n"
            "🏆 **Leaderboard** — Top 10 nach Kontostand\n"
            "🎁 **Daily** — tägliche EHRP Coins\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 **Startguthaben:** {fmt(START_BALANCE)} Coins\n"
            f"🎁 **Daily Bonus:** {fmt(DAILY_REWARD)} Coins\n"
            "🎯 **Einsätze:** 50 • 100 • 250 • 500 Coins\n\n"
            "*Alle Coins sind rein virtuell und haben keinen Echtgeldwert.*"
        ),
        color=CASINO_COLOR,
    )
    embed.set_footer(text="EHRP/VC • Casino System")
    return embed


# =========================================================
# COG / COMMANDS
# =========================================================

class Casino(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Persistentes Hauptpanel nach Bot-Restart.
        self.bot.add_view(CasinoMainView())

    @app_commands.command(
        name="casino_panel",
        description="Erstellt das permanente EHRP/VC Casino-Panel.",
    )
    async def casino_panel(self, interaction: discord.Interaction):
        if not is_casino_admin(interaction):
            return await respond_ephemeral(interaction, content="❌ Keine Berechtigung.")

        if not isinstance(interaction.channel, discord.TextChannel):
            return await respond_ephemeral(
                interaction,
                content="❌ Das Panel kann nur in einem Textkanal erstellt werden.",
            )

        await interaction.response.defer(ephemeral=True)

        embed = main_panel_embed()
        view = CasinoMainView()

        if CASINO_INTRO.exists():
            file = discord.File(CASINO_INTRO, filename="ehrp_casino_intro.gif")
            embed.set_image(url="attachment://ehrp_casino_intro.gif")
            await interaction.channel.send(file=file, embed=embed, view=view)
        else:
            await interaction.channel.send(embed=embed, view=view)

        await interaction.followup.send(
            "✅ Das permanente **EHRP/VC Casino** wurde erstellt.",
            ephemeral=True,
        )

    @app_commands.command(
        name="casino_status",
        description="Zeigt den Status des Casino-Systems.",
    )
    async def casino_status(self, interaction: discord.Interaction):
        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🎰 Casino Status",
                (
                    "🟢 **System online**\n\n"
                    f"👥 Registrierte Spieler: **{fmt(len(casino_data))}**\n"
                    f"💰 Startguthaben: **{fmt(START_BALANCE)}**\n"
                    f"🎁 Daily: **{fmt(DAILY_REWARD)}**\n"
                    f"💾 Datendatei: `{DATA_FILE}`\n"
                    f"🎬 Intro: **{'gefunden' if CASINO_INTRO.exists() else 'nicht gefunden'}**"
                ),
            ),
        )

    @app_commands.command(
        name="casino_coins",
        description="Verwaltet EHRP Coins eines Mitglieds.",
    )
    @app_commands.describe(
        mitglied="Mitglied",
        aktion="Coins setzen, hinzufügen oder entfernen",
        betrag="Anzahl Coins",
    )
    @app_commands.choices(
        aktion=[
            app_commands.Choice(name="Setzen", value="set"),
            app_commands.Choice(name="Hinzufügen", value="add"),
            app_commands.Choice(name="Entfernen", value="remove"),
        ]
    )
    async def casino_coins(
        self,
        interaction: discord.Interaction,
        mitglied: discord.Member,
        aktion: app_commands.Choice[str],
        betrag: app_commands.Range[int, 0, 10_000_000],
    ):
        if not is_casino_admin(interaction):
            return await respond_ephemeral(interaction, content="❌ Keine Berechtigung.")

        async with get_lock(mitglied.id):
            p = get_player(mitglied.id)

            if aktion.value == "set":
                p["balance"] = betrag
            elif aktion.value == "add":
                p["balance"] += betrag
            elif aktion.value == "remove":
                p["balance"] = max(0, p["balance"] - betrag)

            save_data(casino_data)

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "💰 Casino Coins aktualisiert",
                (
                    f"👤 {mitglied.mention}\n"
                    f"🛠️ Aktion: **{aktion.name}**\n"
                    f"💵 Betrag: **{fmt(betrag)} Coins**\n"
                    f"💰 Neuer Kontostand: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
        )

        await casino_log(
            interaction.guild,
            "🛠️ Casino Administration",
            (
                f"{interaction.user.mention} änderte Coins von {mitglied.mention}\n"
                f"Aktion: **{aktion.name}** • Betrag: **{fmt(betrag)}** • Neu: **{fmt(p['balance'])}**"
            ),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Casino(bot))
