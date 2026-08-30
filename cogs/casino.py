from __future__ import annotations

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
# EHRP/VC CASINO V2
# Virtuelle Spielwährung – kein Echtgeldwert.
#
# WICHTIG:
# - Nutzt weiterhin data/casino_data.json bzw. CASINO_DATA_DIR.
# - Vorhandene Coins und alte Gesamtstatistiken werden NICHT zurückgesetzt.
# - Neue V2-Felder werden nur ergänzt.
# =========================================================

START_BALANCE = 1_000
DAILY_REWARD = 250
BET_OPTIONS = [50, 100, 250, 500, 1_000, 2_500, 5_000]
CASINO_COLOR = 0xD4AF37

DATA_DIR = Path(os.getenv("CASINO_DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "casino_data.json"
CASINO_INTRO = Path("assets/ehrp_casino_intro.gif")
CASINO_LOG_CHANNEL_ID = int(os.getenv("CASINO_LOG_CHANNEL_ID", "0"))
OWNER_USER_ID = 1294267376459714621

USER_LOCKS: dict[int, asyncio.Lock] = {}


# =========================================================
# STORAGE / SAFE MIGRATION
# =========================================================

def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")


def load_data() -> dict:
    _ensure_storage()
    try:
        raw = DATA_FILE.read_text(encoding="utf-8").strip()
        parsed = json.loads(raw) if raw else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        print(f"❌ Casino-Daten konnten nicht geladen werden: {type(exc).__name__}: {exc}")
        return {}


def save_data(data: dict) -> None:
    _ensure_storage()
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA_FILE)


casino_data = load_data()


def default_game_stats() -> dict:
    return {
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "won": 0,
        "lost": 0,
        "biggest_win": 0,
    }


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
        "game_stats": {},
        "last_game": None,
    }


def get_player(user_id: int) -> dict:
    uid = str(user_id)

    if uid not in casino_data or not isinstance(casino_data[uid], dict):
        casino_data[uid] = default_player()
        save_data(casino_data)
        return casino_data[uid]

    template = default_player()
    changed = False
    for key, value in template.items():
        if key not in casino_data[uid]:
            casino_data[uid][key] = value.copy() if isinstance(value, dict) else value
            changed = True

    if not isinstance(casino_data[uid].get("game_stats"), dict):
        casino_data[uid]["game_stats"] = {}
        changed = True

    if changed:
        save_data(casino_data)

    return casino_data[uid]


def get_game_stats(player: dict, game: str) -> dict:
    all_stats = player.setdefault("game_stats", {})
    if game not in all_stats or not isinstance(all_stats[game], dict):
        all_stats[game] = default_game_stats()

    for key, value in default_game_stats().items():
        all_stats[game].setdefault(key, value)

    return all_stats[game]


def record_result(player: dict, game: str, outcome: str, amount: int = 0) -> None:
    amount = max(0, int(amount))
    player["games"] = int(player.get("games", 0)) + 1
    player["last_game"] = game

    gs = get_game_stats(player, game)
    gs["games"] += 1

    if outcome == "win":
        player["wins"] = int(player.get("wins", 0)) + 1
        player["total_won"] = int(player.get("total_won", 0)) + amount
        player["biggest_win"] = max(int(player.get("biggest_win", 0)), amount)
        gs["wins"] += 1
        gs["won"] += amount
        gs["biggest_win"] = max(gs["biggest_win"], amount)

    elif outcome == "lose":
        player["losses"] = int(player.get("losses", 0)) + 1
        player["total_lost"] = int(player.get("total_lost", 0)) + amount
        gs["losses"] += 1
        gs["lost"] += amount

    else:
        player["draws"] = int(player.get("draws", 0)) + 1
        gs["draws"] += 1


def get_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_LOCKS:
        USER_LOCKS[user_id] = asyncio.Lock()
    return USER_LOCKS[user_id]


def fmt(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def resolve_bet(user_id: int, selected: int | str) -> int:
    if selected == "all":
        return max(0, int(get_player(user_id)["balance"]))
    return max(0, int(selected))


# =========================================================
# COMMON UI
# =========================================================

def casino_embed(title: str, description: str, user=None) -> discord.Embed:
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


async def respond_ephemeral(interaction: discord.Interaction, *, content=None, embed=None, view=None):
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


async def casino_log(guild, title: str, description: str):
    if guild is None or not CASINO_LOG_CHANNEL_ID:
        return

    channel = guild.get_channel(CASINO_LOG_CHANNEL_ID)

    if not isinstance(channel, discord.TextChannel):
        return

    try:
        await channel.send(
            embed=casino_embed(
                title,
                description,
            )
        )
    except discord.HTTPException:
        pass


async def not_enough(interaction: discord.Interaction, bet: int):
    p = get_player(interaction.user.id)

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "💳 Nicht genügend EHRP Coins",
            (
                f"Benötigt: **{fmt(bet)} Coins**\n"
                f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
            ),
            interaction.user,
        ),
    )


def is_casino_admin(interaction: discord.Interaction) -> bool:
    if interaction.user.id == OWNER_USER_ID:
        return True

    return (
        isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.administrator
    )


GAME_LABELS = {
    "slots": "🎰 Slots",
    "blackjack": "🃏 Blackjack",
    "roulette": "🎡 Roulette",
    "coinflip": "🪙 Coinflip",
    "dice": "🎲 Dice",
    "baccarat": "👑 Baccarat",
    "highlow": "⬆️⬇️ High / Low",
    "mines": "💣 Mines",
    "crash": "🚀 Crash",
}


# =========================================================
# BET SELECT
# =========================================================

class BetSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"{fmt(b)} EHRP Coins",
                value=str(b),
                emoji="💰",
            )
            for b in BET_OPTIONS
        ]

        options.append(
            discord.SelectOption(
                label="ALLES REIN",
                value="all",
                emoji="🔥",
            )
        )

        super().__init__(
            placeholder="💰 Einsatz auswählen",
            min_values=1,
            max_values=1,
            custom_id="ehrp_casino:v2:bet",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(self.view, CasinoMainView):
            return

        selected = self.values[0]
        self.view.user_bets[interaction.user.id] = selected

        if selected == "all":
            amount = get_player(interaction.user.id)["balance"]

            text = (
                f"🔥 **ALLES REIN** gewählt — "
                f"aktuell **{fmt(amount)} Coins**."
            )

        else:
            text = (
                f"✅ Einsatz: "
                f"**{fmt(int(selected))} EHRP Coins**."
            )

        await respond_ephemeral(
            interaction,
            content=text,
        )


# =========================================================
# SLOTS / DICE
# =========================================================

SLOT_SYMBOLS = [
    "🍒",
    "🍋",
    "🔔",
    "BAR",
    "👑",
    "💎",
    "7️⃣",
]


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


async def play_slots(interaction: discord.Interaction, bet: int):
    async with get_lock(interaction.user.id):
        p = get_player(interaction.user.id)

        if bet <= 0:
            return await respond_ephemeral(
                interaction,
                content="❌ Sie haben keine EHRP Coins für diesen Einsatz.",
            )

        if p["balance"] < bet:
            return await not_enough(interaction, bet)

        result = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        mult = slot_multiplier(result)

        if mult > 0:
            payout = int(bet * mult)
            profit = payout - bet

            p["balance"] += profit

            if profit > 0:
                record_result(p, "slots", "win", profit)
                status = (
                    f"✨ **GEWINN!**\n"
                    f"Multiplikator: **x{mult:g}**\n"
                    f"Auszahlung: **{fmt(payout)} Coins**\n"
                    f"Nettogewinn: **+{fmt(profit)} Coins**"
                )
            elif profit == 0:
                record_result(p, "slots", "draw", 0)
                status = (
                    f"⚖️ **Einsatz zurück!**\n"
                    f"Auszahlung: **{fmt(payout)} Coins**"
                )
            else:
                loss = abs(profit)
                record_result(p, "slots", "lose", loss)
                status = f"❌ **Verlust: -{fmt(loss)} Coins**"
        else:
            p["balance"] -= bet
            record_result(p, "slots", "lose", bet)
            status = f"❌ **Kein Gewinn**\nVerlust: **-{fmt(bet)} Coins**"

        save_data(casino_data)

    embed = casino_embed(
        "🎰 EHRP Slots",
        (
            f"## ┃ {result[0]} ┃ {result[1]} ┃ {result[2]} ┃\n\n"
            f"{status}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Guthaben: **{fmt(p['balance'])} Coins**\n"
            f"🎯 Einsatz: **{fmt(bet)} Coins**"
        ),
        interaction.user,
    )

    await respond_ephemeral(
        interaction,
        embed=embed,
        view=RepeatGameView(
            interaction.user.id,
            "slots",
            bet,
        ),
    )

    await casino_log(
        interaction.guild,
        "🎰 Slots",
        (
            f"{interaction.user.mention} • "
            f"Einsatz **{fmt(bet)}** • "
            f"{' | '.join(result)}"
        ),
    )


async def play_dice(interaction: discord.Interaction, bet: int):
    async with get_lock(interaction.user.id):
        p = get_player(interaction.user.id)

        if bet <= 0:
            return await respond_ephemeral(
                interaction,
                content="❌ Sie haben keine EHRP Coins für diesen Einsatz.",
            )

        if p["balance"] < bet:
            return await not_enough(interaction, bet)

        user_roll = random.randint(1, 6)
        casino_roll = random.randint(1, 6)

        if user_roll > casino_roll:
            p["balance"] += bet
            record_result(p, "dice", "win", bet)
            status = f"✅ **Sie gewinnen!**\n+**{fmt(bet)} Coins**"

        elif user_roll < casino_roll:
            p["balance"] -= bet
            record_result(p, "dice", "lose", bet)
            status = f"❌ **Casino gewinnt.**\n-**{fmt(bet)} Coins**"

        else:
            record_result(p, "dice", "draw", 0)
            status = "⚖️ **Unentschieden.**\nDer Einsatz bleibt erhalten."

        save_data(casino_data)

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "🎲 EHRP Dice",
            (
                f"### Ihre Zahl\n"
                f"# 🎲 {user_roll}\n\n"
                f"### Casino\n"
                f"# 🎲 {casino_roll}\n\n"
                f"{status}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 Guthaben: **{fmt(p['balance'])} Coins**\n"
                f"🎯 Einsatz: **{fmt(bet)} Coins**"
            ),
            interaction.user,
        ),
        view=RepeatGameView(
            interaction.user.id,
            "dice",
            bet,
        ),
    )

    await casino_log(
        interaction.guild,
        "🎲 Dice",
        (
            f"{interaction.user.mention} • "
            f"{user_roll} : {casino_roll} • "
            f"Einsatz **{fmt(bet)}**"
        ),
    )


# =========================================================
# COINFLIP
# =========================================================

class CoinflipView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    async def resolve(
        self,
        interaction: discord.Interaction,
        choice: str,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde wurde bereits beendet.",
            )

        async with get_lock(interaction.user.id):
            p = get_player(interaction.user.id)

            if self.bet <= 0:
                return await respond_ephemeral(
                    interaction,
                    content="❌ Ungültiger Einsatz.",
                )

            if p["balance"] < self.bet:
                return await not_enough(interaction, self.bet)

            self.finished = True
            result = random.choice(["Kopf", "Zahl"])

            if choice == result:
                p["balance"] += self.bet
                record_result(
                    p,
                    "coinflip",
                    "win",
                    self.bet,
                )
                status = (
                    f"✅ **Gewonnen!**\n"
                    f"Gewinn: **+{fmt(self.bet)} Coins**"
                )
            else:
                p["balance"] -= self.bet
                record_result(
                    p,
                    "coinflip",
                    "lose",
                    self.bet,
                )
                status = (
                    f"❌ **Verloren.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**"
                )

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=casino_embed(
                "🪙 EHRP Coinflip",
                (
                    f"# 🪙 {result}\n\n"
                    f"Ihre Wahl: **{choice}**\n\n"
                    f"{status}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "🪙 Coinflip",
            (
                f"{interaction.user.mention} • "
                f"Einsatz **{fmt(self.bet)}** • "
                f"Wahl **{choice}** • "
                f"Ergebnis **{result}**"
            ),
        )

    @discord.ui.button(
        label="Kopf",
        emoji="👑",
        style=discord.ButtonStyle.primary,
    )
    async def heads(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(interaction, "Kopf")

    @discord.ui.button(
        label="Zahl",
        emoji="🪙",
        style=discord.ButtonStyle.secondary,
    )
    async def tails(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(interaction, "Zahl")


async def start_coinflip(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(interaction.user.id)

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(interaction, bet)

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "🪙 EHRP Coinflip",
            (
                f"🎯 Einsatz: **{fmt(bet)} EHRP Coins**\n\n"
                f"Wählen Sie **Kopf** oder **Zahl**."
            ),
            interaction.user,
        ),
        view=CoinflipView(
            interaction.user.id,
            bet,
        ),
    )


# =========================================================
# BLACKJACK
# =========================================================

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
]


def new_deck() -> list[str]:
    deck = [
        f"{rank}{suit}"
        for suit in SUITS
        for rank in RANKS
    ]
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


def hand_text(
    hand: list[str],
    hide_second: bool = False,
) -> str:
    if hide_second and len(hand) > 1:
        return f"`{hand[0]}` `??`"

    return " ".join(
        f"`{card}`"
        for card in hand
    )


class BlackjackView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=180)

        self.owner_id = owner_id
        self.bet = bet
        self.deck = new_deck()

        self.player_hand = [
            self.deck.pop(),
            self.deck.pop(),
        ]

        self.dealer_hand = [
            self.deck.pop(),
            self.deck.pop(),
        ]

        self.finished = False

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Blackjack-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    def game_embed(
        self,
        user,
        reveal_dealer: bool = False,
        result: str | None = None,
    ) -> discord.Embed:
        player_value = hand_value(self.player_hand)

        if reveal_dealer:
            dealer_value = hand_value(self.dealer_hand)
        else:
            dealer_value = hand_value(
                [self.dealer_hand[0]]
            )

        description = (
            f"### 🃏 Ihre Karten\n"
            f"{hand_text(self.player_hand)}\n"
            f"**Wert: {player_value}**\n\n"
            f"### 🎩 Dealer\n"
            f"{hand_text(self.dealer_hand, hide_second=not reveal_dealer)}\n"
            f"**Wert: {dealer_value}**\n\n"
            f"🎯 Einsatz: **{fmt(self.bet)} Coins**"
        )

        if result:
            description += (
                f"\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{result}"
            )

        return casino_embed(
            "🃏 EHRP Blackjack",
            description,
            user,
        )

    async def finish(
        self,
        interaction: discord.Interaction,
        outcome: str,
    ):
        if self.finished:
            return

        async with get_lock(self.owner_id):
            if self.finished:
                return

            self.finished = True
            p = get_player(self.owner_id)

            if outcome == "blackjack":
                profit = int(self.bet * 1.5)
                p["balance"] += profit
                record_result(
                    p,
                    "blackjack",
                    "win",
                    profit,
                )

                result = (
                    f"✨ **BLACKJACK!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**"
                )

            elif outcome == "win":
                profit = self.bet
                p["balance"] += profit
                record_result(
                    p,
                    "blackjack",
                    "win",
                    profit,
                )

                result = (
                    f"✅ **Sie gewinnen!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**"
                )

            elif outcome == "draw":
                record_result(
                    p,
                    "blackjack",
                    "draw",
                    0,
                )

                result = (
                    "⚖️ **Push / Unentschieden.**\n"
                    "Der Einsatz bleibt erhalten."
                )

            else:
                p["balance"] -= self.bet
                record_result(
                    p,
                    "blackjack",
                    "lose",
                    self.bet,
                )

                result = (
                    f"❌ **Dealer gewinnt.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**"
                )

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        result += (
            f"\n\n💰 Guthaben: "
            f"**{fmt(p['balance'])} Coins**"
        )

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user,
                reveal_dealer=True,
                result=result,
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "🃏 Blackjack",
            (
                f"{interaction.user.mention} • "
                f"Einsatz **{fmt(self.bet)}** • "
                f"Ergebnis **{outcome}**"
            ),
        )

    @discord.ui.button(
        label="Hit",
        emoji="➕",
        style=discord.ButtonStyle.primary,
    )
    async def hit(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if self.finished:
            return

        self.player_hand.append(
            self.deck.pop()
        )

        value = hand_value(
            self.player_hand
        )

        if value > 21:
            return await self.finish(
                interaction,
                "lose",
            )

        if value == 21:
            return await self.stand_logic(
                interaction
            )

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user
            ),
            view=self,
        )

    @discord.ui.button(
        label="Stand",
        emoji="✋",
        style=discord.ButtonStyle.secondary,
    )
    async def stand(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.stand_logic(
            interaction
        )

    async def stand_logic(
        self,
        interaction: discord.Interaction,
    ):
        if self.finished:
            return

        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(
                self.deck.pop()
            )

        player_value = hand_value(
            self.player_hand
        )

        dealer_value = hand_value(
            self.dealer_hand
        )

        if dealer_value > 21:
            outcome = "win"
        elif player_value > dealer_value:
            outcome = "win"
        elif player_value < dealer_value:
            outcome = "lose"
        else:
            outcome = "draw"

        await self.finish(
            interaction,
            outcome,
        )


async def start_blackjack(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(interaction.user.id)

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    view = BlackjackView(
        interaction.user.id,
        bet,
    )

    player_natural = (
        hand_value(view.player_hand) == 21
    )

    dealer_natural = (
        hand_value(view.dealer_hand) == 21
    )

    if player_natural:
        await interaction.response.send_message(
            embed=view.game_embed(
                interaction.user,
                reveal_dealer=True,
            ),
            view=view,
            ephemeral=True,
        )

        async with get_lock(interaction.user.id):
            p = get_player(interaction.user.id)

            view.finished = True

            if dealer_natural:
                record_result(
                    p,
                    "blackjack",
                    "draw",
                    0,
                )

                result = (
                    "⚖️ **Beide haben Blackjack. Push.**"
                )

            else:
                profit = int(bet * 1.5)

                p["balance"] += profit

                record_result(
                    p,
                    "blackjack",
                    "win",
                    profit,
                )

                result = (
                    f"✨ **BLACKJACK!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**"
                )

            save_data(casino_data)

        for item in view.children:
            item.disabled = True

        await interaction.edit_original_response(
            embed=view.game_embed(
                interaction.user,
                reveal_dealer=True,
                result=(
                    f"{result}\n\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                ),
            ),
            view=view,
        )

        return

    await interaction.response.send_message(
        embed=view.game_embed(
            interaction.user
        ),
        view=view,
        ephemeral=True,
    )


# =========================================================
# ROULETTE
# =========================================================

ROULETTE_RED = {
    1, 3, 5, 7, 9,
    12, 14, 16, 18,
    19, 21, 23, 25, 27,
    30, 32, 34, 36,
}


def roulette_color(number: int) -> str:
    if number == 0:
        return "🟢 Grün"

    if number in ROULETTE_RED:
        return "🔴 Rot"

    return "⚫ Schwarz"


class RouletteView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Roulette-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    async def resolve(
        self,
        interaction: discord.Interaction,
        choice: str,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde wurde bereits beendet.",
            )

        async with get_lock(self.owner_id):
            p = get_player(self.owner_id)

            if p["balance"] < self.bet:
                return await not_enough(
                    interaction,
                    self.bet,
                )

            self.finished = True
            number = random.randint(0, 36)
            color = roulette_color(number)

            won = False
            multiplier = 0

            if choice == "red":
                won = number in ROULETTE_RED
                multiplier = 1

            elif choice == "black":
                won = (
                    number != 0
                    and number not in ROULETTE_RED
                )
                multiplier = 1

            elif choice == "even":
                won = (
                    number != 0
                    and number % 2 == 0
                )
                multiplier = 1

            elif choice == "odd":
                won = (
                    number != 0
                    and number % 2 == 1
                )
                multiplier = 1

            elif choice == "zero":
                won = number == 0
                multiplier = 35

            if won:
                profit = self.bet * multiplier
                p["balance"] += profit

                record_result(
                    p,
                    "roulette",
                    "win",
                    profit,
                )

                status = (
                    f"✅ **Gewonnen!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**"
                )

            else:
                p["balance"] -= self.bet

                record_result(
                    p,
                    "roulette",
                    "lose",
                    self.bet,
                )

                status = (
                    f"❌ **Verloren.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**"
                )

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=casino_embed(
                "🎡 EHRP Roulette",
                (
                    f"# {number}\n"
                    f"### {color}\n\n"
                    f"{status}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Guthaben: **{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
            view=self,
        )

    @discord.ui.button(
        label="Rot",
        emoji="🔴",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def red(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "red",
        )

    @discord.ui.button(
        label="Schwarz",
        emoji="⚫",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def black(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "black",
        )

    @discord.ui.button(
        label="Gerade",
        emoji="2️⃣",
        style=discord.ButtonStyle.primary,
        row=1,
    )
    async def even(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "even",
        )

    @discord.ui.button(
        label="Ungerade",
        emoji="3️⃣",
        style=discord.ButtonStyle.primary,
        row=1,
    )
    async def odd(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "odd",
        )

    @discord.ui.button(
        label="0",
        emoji="🟢",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def zero(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "zero",
        )


async def start_roulette(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(interaction.user.id)

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "🎡 EHRP Roulette",
            (
                f"🎯 Einsatz: **{fmt(bet)} Coins**\n\n"
                f"Wählen Sie Ihren Einsatz:\n\n"
                f"🔴 **Rot** — x2 Auszahlung\n"
                f"⚫ **Schwarz** — x2 Auszahlung\n"
                f"2️⃣ **Gerade** — x2 Auszahlung\n"
                f"3️⃣ **Ungerade** — x2 Auszahlung\n"
                f"🟢 **0** — x36 Auszahlung"
            ),
            interaction.user,
        ),
        view=RouletteView(
            interaction.user.id,
            bet,
        ),
    )

# =========================================================
# BACCARAT
# =========================================================

BACCARAT_SUITS = ["♠", "♥", "♦", "♣"]
BACCARAT_RANKS = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
]


def baccarat_deck() -> list[str]:
    deck = [
        f"{rank}{suit}"
        for suit in BACCARAT_SUITS
        for rank in BACCARAT_RANKS
    ]

    random.shuffle(deck)
    return deck


def baccarat_card_value(card: str) -> int:
    rank = card[:-1]

    if rank == "A":
        return 1

    if rank in ("10", "J", "Q", "K"):
        return 0

    return int(rank)


def baccarat_value(hand: list[str]) -> int:
    return sum(
        baccarat_card_value(card)
        for card in hand
    ) % 10


def baccarat_hand_text(hand: list[str]) -> str:
    return " ".join(
        f"`{card}`"
        for card in hand
    )


class BaccaratView(discord.ui.View):
    def __init__(self, owner_id: int, bet: int):
        super().__init__(timeout=120)

        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Baccarat-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    async def resolve(
        self,
        interaction: discord.Interaction,
        choice: str,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde wurde bereits beendet.",
            )

        async with get_lock(self.owner_id):
            p = get_player(self.owner_id)

            if p["balance"] < self.bet:
                return await not_enough(
                    interaction,
                    self.bet,
                )

            self.finished = True

            deck = baccarat_deck()

            player_hand = [
                deck.pop(),
                deck.pop(),
            ]

            banker_hand = [
                deck.pop(),
                deck.pop(),
            ]

            player_value = baccarat_value(
                player_hand
            )

            banker_value = baccarat_value(
                banker_hand
            )

            natural = (
                player_value >= 8
                or banker_value >= 8
            )

            if not natural:
                player_third_value = None

                if player_value <= 5:
                    player_third = deck.pop()
                    player_hand.append(player_third)

                    player_third_value = baccarat_card_value(
                        player_third
                    )

                    player_value = baccarat_value(
                        player_hand
                    )

                banker_draw = False

                if player_third_value is None:
                    banker_draw = banker_value <= 5

                elif banker_value <= 2:
                    banker_draw = True

                elif banker_value == 3:
                    banker_draw = (
                        player_third_value != 8
                    )

                elif banker_value == 4:
                    banker_draw = (
                        2 <= player_third_value <= 7
                    )

                elif banker_value == 5:
                    banker_draw = (
                        4 <= player_third_value <= 7
                    )

                elif banker_value == 6:
                    banker_draw = (
                        6 <= player_third_value <= 7
                    )

                if banker_draw:
                    banker_hand.append(
                        deck.pop()
                    )

                    banker_value = baccarat_value(
                        banker_hand
                    )

            if player_value > banker_value:
                result = "player"
                result_name = "Spieler"

            elif banker_value > player_value:
                result = "banker"
                result_name = "Bank"

            else:
                result = "tie"
                result_name = "Unentschieden"

            if choice == result:
                if result == "tie":
                    profit = self.bet * 8

                else:
                    profit = self.bet

                p["balance"] += profit

                record_result(
                    p,
                    "baccarat",
                    "win",
                    profit,
                )

                status = (
                    f"✅ **Gewonnen!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**"
                )

            else:
                p["balance"] -= self.bet

                record_result(
                    p,
                    "baccarat",
                    "lose",
                    self.bet,
                )

                status = (
                    f"❌ **Verloren.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**"
                )

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=casino_embed(
                "👑 EHRP Baccarat",
                (
                    f"### 👤 Spieler\n"
                    f"{baccarat_hand_text(player_hand)}\n"
                    f"**Wert: {player_value}**\n\n"
                    f"### 🏦 Bank\n"
                    f"{baccarat_hand_text(banker_hand)}\n"
                    f"**Wert: {banker_value}**\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Ergebnis: **{result_name}**\n\n"
                    f"{status}\n\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "👑 Baccarat",
            (
                f"{interaction.user.mention} • "
                f"Einsatz **{fmt(self.bet)}** • "
                f"Wahl **{choice}** • "
                f"Ergebnis **{result_name}**"
            ),
        )

    @discord.ui.button(
        label="Spieler",
        emoji="👤",
        style=discord.ButtonStyle.primary,
    )
    async def player(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "player",
        )

    @discord.ui.button(
        label="Bank",
        emoji="🏦",
        style=discord.ButtonStyle.secondary,
    )
    async def banker(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "banker",
        )

    @discord.ui.button(
        label="Unentschieden",
        emoji="⚖️",
        style=discord.ButtonStyle.success,
    )
    async def tie(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "tie",
        )


async def start_baccarat(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(
        interaction.user.id
    )

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "👑 EHRP Baccarat",
            (
                f"🎯 Einsatz: **{fmt(bet)} Coins**\n\n"
                f"Worauf setzen Sie?\n\n"
                f"👤 **Spieler** — 1:1\n"
                f"🏦 **Bank** — 1:1\n"
                f"⚖️ **Unentschieden** — 8:1"
            ),
            interaction.user,
        ),
        view=BaccaratView(
            interaction.user.id,
            bet,
        ),
    )


# =========================================================
# HIGH / LOW
# =========================================================

HIGHLOW_SUITS = [
    "♠",
    "♥",
    "♦",
    "♣",
]

HIGHLOW_RANKS = [
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
]


def highlow_deck() -> list[str]:
    deck = [
        f"{rank}{suit}"
        for suit in HIGHLOW_SUITS
        for rank in HIGHLOW_RANKS
    ]

    random.shuffle(deck)
    return deck


def highlow_card_value(card: str) -> int:
    rank = card[:-1]

    values = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14,
    }

    return values[rank]


class HighLowView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        bet: int,
    ):
        super().__init__(timeout=120)

        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

        self.deck = highlow_deck()
        self.current_card = self.deck.pop()

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses High/Low-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    def game_embed(
        self,
        user,
        result: str | None = None,
    ) -> discord.Embed:
        description = (
            f"## Aktuelle Karte\n"
            f"# 🃏 `{self.current_card}`\n\n"
            f"Ist die nächste Karte "
            f"**höher** oder **niedriger**?\n\n"
            f"🎯 Einsatz: **{fmt(self.bet)} Coins**"
        )

        if result:
            description += (
                f"\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{result}"
            )

        return casino_embed(
            "⬆️⬇️ EHRP High / Low",
            description,
            user,
        )

    async def resolve(
        self,
        interaction: discord.Interaction,
        choice: str,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde wurde bereits beendet.",
            )

        async with get_lock(
            self.owner_id
        ):
            p = get_player(
                self.owner_id
            )

            if p["balance"] < self.bet:
                return await not_enough(
                    interaction,
                    self.bet,
                )

            self.finished = True

            next_card = self.deck.pop()

            current_value = highlow_card_value(
                self.current_card
            )

            next_value = highlow_card_value(
                next_card
            )

            if next_value > current_value:
                actual = "higher"
                actual_text = "Höher"

            elif next_value < current_value:
                actual = "lower"
                actual_text = "Niedriger"

            else:
                actual = "same"
                actual_text = "Gleich"

            if actual == "same":
                record_result(
                    p,
                    "highlow",
                    "draw",
                    0,
                )

                status = (
                    "⚖️ **Gleicher Kartenwert!**\n"
                    "Kein Gewinn und kein Verlust."
                )

            elif choice == actual:
                p["balance"] += self.bet

                record_result(
                    p,
                    "highlow",
                    "win",
                    self.bet,
                )

                status = (
                    f"✅ **Richtig!**\n"
                    f"Gewinn: **+{fmt(self.bet)} Coins**"
                )

            else:
                p["balance"] -= self.bet

                record_result(
                    p,
                    "highlow",
                    "lose",
                    self.bet,
                )

                status = (
                    f"❌ **Falsch.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**"
                )

            save_data(casino_data)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=casino_embed(
                "⬆️⬇️ EHRP High / Low",
                (
                    f"### Erste Karte\n"
                    f"# 🃏 `{self.current_card}`\n\n"
                    f"### Nächste Karte\n"
                    f"# 🃏 `{next_card}`\n\n"
                    f"Ergebnis: **{actual_text}**\n\n"
                    f"{status}\n\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                ),
                interaction.user,
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "⬆️⬇️ High / Low",
            (
                f"{interaction.user.mention} • "
                f"{self.current_card} → {next_card} • "
                f"Einsatz **{fmt(self.bet)}**"
            ),
        )

    @discord.ui.button(
        label="Höher",
        emoji="⬆️",
        style=discord.ButtonStyle.success,
    )
    async def higher(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "higher",
        )

    @discord.ui.button(
        label="Niedriger",
        emoji="⬇️",
        style=discord.ButtonStyle.danger,
    )
    async def lower(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.resolve(
            interaction,
            "lower",
        )


async def start_highlow(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(
        interaction.user.id
    )

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    view = HighLowView(
        interaction.user.id,
        bet,
    )

    await respond_ephemeral(
        interaction,
        embed=view.game_embed(
            interaction.user
        ),
        view=view,
    )


# =========================================================
# MINES
# =========================================================

class MineButton(discord.ui.Button):
    def __init__(
        self,
        position: int,
    ):
        super().__init__(
            label="?",
            style=discord.ButtonStyle.secondary,
            row=position // 5,
        )

        self.position = position

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        view = self.view

        if not isinstance(
            view,
            MinesView,
        ):
            return

        await view.pick(
            interaction,
            self,
        )


class MinesView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        bet: int,
    ):
        super().__init__(timeout=180)

        self.owner_id = owner_id
        self.bet = bet
        self.finished = False

        self.mine_positions = set(
            random.sample(
                range(20),
                4,
            )
        )

        self.opened: set[int] = set()

        for position in range(20):
            self.add_item(
                MineButton(
                    position
                )
            )

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Mines-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    def multiplier(self) -> float:
        safe = len(self.opened)

        multipliers = {
            0: 1.00,
            1: 1.15,
            2: 1.35,
            3: 1.60,
            4: 1.90,
            5: 2.25,
            6: 2.70,
            7: 3.25,
            8: 4.00,
            9: 5.00,
            10: 6.30,
            11: 8.00,
            12: 10.50,
            13: 14.00,
            14: 20.00,
            15: 30.00,
            16: 50.00,
        }

        return multipliers.get(
            safe,
            1.0,
        )

    def potential_profit(self) -> int:
        return max(
            0,
            int(
                self.bet
                * self.multiplier()
            )
            - self.bet,
        )

    def game_embed(
        self,
        user,
        message: str | None = None,
    ) -> discord.Embed:
        description = (
            f"💣 Minen: **4**\n"
            f"💎 Sichere Felder geöffnet: "
            f"**{len(self.opened)}**\n"
            f"📈 Multiplikator: "
            f"**x{self.multiplier():.2f}**\n"
            f"💰 Aktueller möglicher Gewinn: "
            f"**+{fmt(self.potential_profit())} Coins**\n"
            f"🎯 Einsatz: **{fmt(self.bet)} Coins**\n\n"
            f"Öffnen Sie Felder und steigen Sie "
            f"rechtzeitig aus."
        )

        if message:
            description += (
                f"\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{message}"
            )

        return casino_embed(
            "💣 EHRP Mines",
            description,
            user,
        )

    async def pick(
        self,
        interaction: discord.Interaction,
        button: MineButton,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde ist bereits beendet.",
            )

        if button.position in self.opened:
            return await respond_ephemeral(
                interaction,
                content="❌ Dieses Feld wurde bereits geöffnet.",
            )

        async with get_lock(
            self.owner_id
        ):
            p = get_player(
                self.owner_id
            )

            if p["balance"] < self.bet:
                return await not_enough(
                    interaction,
                    self.bet,
                )

            if button.position in self.mine_positions:
                self.finished = True

                p["balance"] -= self.bet

                record_result(
                    p,
                    "mines",
                    "lose",
                    self.bet,
                )

                save_data(
                    casino_data
                )

                button.label = "💣"
                button.style = discord.ButtonStyle.danger

                for item in self.children:
                    if isinstance(
                        item,
                        MineButton,
                    ):
                        item.disabled = True

                        if (
                            item.position
                            in self.mine_positions
                        ):
                            item.label = "💣"
                            item.style = (
                                discord.ButtonStyle.danger
                            )

                message = (
                    f"💥 **BOOM! Mine getroffen.**\n"
                    f"Verlust: **-{fmt(self.bet)} Coins**\n\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                )

            else:
                self.opened.add(
                    button.position
                )

                button.label = "💎"
                button.style = (
                    discord.ButtonStyle.success
                )
                button.disabled = True

                message = (
                    f"💎 **Sicher!**\n"
                    f"Sie können weiterspielen "
                    f"oder Ihren Gewinn auszahlen."
                )

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user,
                message,
            ),
            view=self,
        )

    @discord.ui.button(
        label="Gewinn auszahlen",
        emoji="💰",
        style=discord.ButtonStyle.success,
        row=4,
    )
    async def cashout(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde ist bereits beendet.",
            )

        if not self.opened:
            return await respond_ephemeral(
                interaction,
                content="❌ Öffnen Sie zuerst mindestens ein Feld.",
            )

        async with get_lock(
            self.owner_id
        ):
            if self.finished:
                return

            self.finished = True

            p = get_player(
                self.owner_id
            )

            profit = self.potential_profit()

            p["balance"] += profit

            if profit > 0:
                record_result(
                    p,
                    "mines",
                    "win",
                    profit,
                )
            else:
                record_result(
                    p,
                    "mines",
                    "draw",
                    0,
                )

            save_data(
                casino_data
            )

        for item in self.children:
            item.disabled = True

            if isinstance(
                item,
                MineButton,
            ):
                if (
                    item.position
                    in self.mine_positions
                ):
                    item.label = "💣"

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user,
                (
                    f"💰 **Ausgezahlt!**\n"
                    f"Gewinn: **+{fmt(profit)} Coins**\n\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                ),
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "💣 Mines",
            (
                f"{interaction.user.mention} • "
                f"Einsatz **{fmt(self.bet)}** • "
                f"Sichere Felder **{len(self.opened)}** • "
                f"Gewinn **{fmt(profit)}**"
            ),
        )


async def start_mines(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(
        interaction.user.id
    )

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    view = MinesView(
        interaction.user.id,
        bet,
    )

    await respond_ephemeral(
        interaction,
        embed=view.game_embed(
            interaction.user
        ),
        view=view,
    )

# =========================================================
# CRASH
# =========================================================

class CrashView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        bet: int,
    ):
        super().__init__(timeout=180)

        self.owner_id = owner_id
        self.bet = bet
        self.finished = False
        self.started = False

        self.multiplier = 1.00
        self.crash_at = self.generate_crash_point()

        self.message: discord.InteractionMessage | None = None
        self.task: asyncio.Task | None = None

    @staticmethod
    def generate_crash_point() -> float:
        roll = random.random()

        if roll < 0.03:
            return 1.00

        value = 0.97 / max(
            0.01,
            1.0 - roll,
        )

        return round(
            min(
                max(value, 1.01),
                50.00,
            ),
            2,
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Crash-Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    def game_embed(
        self,
        user,
        message: str | None = None,
    ) -> discord.Embed:
        description = (
            f"# 🚀 x{self.multiplier:.2f}\n\n"
            f"🎯 Einsatz: **{fmt(self.bet)} Coins**\n"
            f"💰 Aktueller möglicher Gewinn: "
            f"**+{fmt(max(0, int(self.bet * self.multiplier) - self.bet))} Coins**\n\n"
            f"Steigen Sie aus, bevor der Kurs abstürzt."
        )

        if message:
            description += (
                f"\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{message}"
            )

        return casino_embed(
            "🚀 EHRP Crash",
            description,
            user,
        )

    async def begin(
        self,
        interaction: discord.Interaction,
    ):
        if self.started:
            return

        async with get_lock(
            self.owner_id
        ):
            p = get_player(
                self.owner_id
            )

            if p["balance"] < self.bet:
                return await not_enough(
                    interaction,
                    self.bet,
                )

            self.started = True

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user,
                "🟢 **Runde läuft!**",
            ),
            view=self,
        )

        try:
            self.message = (
                await interaction.original_response()
            )
        except discord.HTTPException:
            self.message = None

        self.task = asyncio.create_task(
            self.run_game(
                interaction.user,
                interaction.guild,
            )
        )

    async def run_game(
        self,
        user,
        guild,
    ):
        try:
            while not self.finished:
                await asyncio.sleep(1)

                if self.finished:
                    return

                growth = random.uniform(
                    0.08,
                    0.30,
                )

                self.multiplier = round(
                    self.multiplier + growth,
                    2,
                )

                if self.multiplier >= self.crash_at:
                    self.multiplier = self.crash_at

                    async with get_lock(
                        self.owner_id
                    ):
                        if self.finished:
                            return

                        self.finished = True

                        p = get_player(
                            self.owner_id
                        )

                        p["balance"] -= self.bet

                        record_result(
                            p,
                            "crash",
                            "lose",
                            self.bet,
                        )

                        save_data(
                            casino_data
                        )

                    for item in self.children:
                        item.disabled = True

                    if self.message is not None:
                        try:
                            await self.message.edit(
                                embed=self.game_embed(
                                    user,
                                    (
                                        f"💥 **CRASH bei x{self.crash_at:.2f}!**\n"
                                        f"Verlust: **-{fmt(self.bet)} Coins**\n\n"
                                        f"💰 Guthaben: "
                                        f"**{fmt(p['balance'])} Coins**"
                                    ),
                                ),
                                view=self,
                            )
                        except discord.HTTPException:
                            pass

                    await casino_log(
                        guild,
                        "🚀 Crash",
                        (
                            f"<@{self.owner_id}> • "
                            f"Einsatz **{fmt(self.bet)}** • "
                            f"Crash **x{self.crash_at:.2f}**"
                        ),
                    )

                    return

                if self.message is not None:
                    try:
                        await self.message.edit(
                            embed=self.game_embed(
                                user,
                                "🟢 **Runde läuft...**",
                            ),
                            view=self,
                        )
                    except discord.HTTPException:
                        pass

        except asyncio.CancelledError:
            return

    @discord.ui.button(
        label="START",
        emoji="🚀",
        style=discord.ButtonStyle.success,
    )
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        button.disabled = True

        await self.begin(
            interaction
        )

    @discord.ui.button(
        label="AUSSTEIGEN",
        emoji="💰",
        style=discord.ButtonStyle.danger,
    )
    async def cashout(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not self.started:
            return await respond_ephemeral(
                interaction,
                content="❌ Starten Sie zuerst die Runde.",
            )

        if self.finished:
            return await respond_ephemeral(
                interaction,
                content="❌ Diese Runde ist bereits beendet.",
            )

        async with get_lock(
            self.owner_id
        ):
            if self.finished:
                return

            self.finished = True

            p = get_player(
                self.owner_id
            )

            payout = int(
                self.bet
                * self.multiplier
            )

            profit = max(
                0,
                payout - self.bet,
            )

            p["balance"] += profit

            if profit > 0:
                record_result(
                    p,
                    "crash",
                    "win",
                    profit,
                )
            else:
                record_result(
                    p,
                    "crash",
                    "draw",
                    0,
                )

            save_data(
                casino_data
            )

        if (
            self.task is not None
            and not self.task.done()
        ):
            self.task.cancel()

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=self.game_embed(
                interaction.user,
                (
                    f"💰 **RECHTZEITIG AUSGESTIEGEN!**\n"
                    f"Multiplikator: **x{self.multiplier:.2f}**\n"
                    f"Auszahlung: **{fmt(payout)} Coins**\n"
                    f"Nettogewinn: **+{fmt(profit)} Coins**\n\n"
                    f"💰 Guthaben: "
                    f"**{fmt(p['balance'])} Coins**"
                ),
            ),
            view=self,
        )

        await casino_log(
            interaction.guild,
            "🚀 Crash",
            (
                f"{interaction.user.mention} • "
                f"Einsatz **{fmt(self.bet)}** • "
                f"Cashout **x{self.multiplier:.2f}** • "
                f"Gewinn **{fmt(profit)}**"
            ),
        )


async def start_crash(
    interaction: discord.Interaction,
    bet: int,
):
    p = get_player(
        interaction.user.id
    )

    if bet <= 0:
        return await respond_ephemeral(
            interaction,
            content="❌ Sie haben keine Coins für diesen Einsatz.",
        )

    if p["balance"] < bet:
        return await not_enough(
            interaction,
            bet,
        )

    view = CrashView(
        interaction.user.id,
        bet,
    )

    await respond_ephemeral(
        interaction,
        embed=view.game_embed(
            interaction.user,
            (
                "Drücken Sie **START**.\n"
                "Danach steigt der Multiplikator automatisch."
            ),
        ),
        view=view,
    )


# =========================================================
# REPEAT GAME VIEW
# =========================================================

class RepeatGameView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        game: str,
        bet: int,
    ):
        super().__init__(timeout=180)

        self.owner_id = owner_id
        self.game = game
        self.bet = bet

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Dieses Spiel gehört nicht Ihnen.",
            )
            return False

        return True

    @discord.ui.button(
        label="Nochmal spielen",
        emoji="🔄",
        style=discord.ButtonStyle.success,
    )
    async def repeat(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        p = get_player(
            interaction.user.id
        )

        bet = min(
            self.bet,
            int(p["balance"]),
        )

        if bet <= 0:
            return await respond_ephemeral(
                interaction,
                content="❌ Sie haben keine EHRP Coins mehr.",
            )

        if self.game == "slots":
            await play_slots(
                interaction,
                bet,
            )

        elif self.game == "dice":
            await play_dice(
                interaction,
                bet,
            )

        elif self.game == "blackjack":
            await start_blackjack(
                interaction,
                bet,
            )

        elif self.game == "coinflip":
            await start_coinflip(
                interaction,
                bet,
            )

        elif self.game == "roulette":
            await start_roulette(
                interaction,
                bet,
            )

        elif self.game == "baccarat":
            await start_baccarat(
                interaction,
                bet,
            )

        elif self.game == "highlow":
            await start_highlow(
                interaction,
                bet,
            )

        elif self.game == "mines":
            await start_mines(
                interaction,
                bet,
            )

        elif self.game == "crash":
            await start_crash(
                interaction,
                bet,
            )

    @discord.ui.button(
        label="Zurück zum Casino",
        emoji="🎰",
        style=discord.ButtonStyle.secondary,
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await respond_ephemeral(
            interaction,
            embed=personal_casino_embed(
                interaction.user
            ),
            view=PersonalCasinoView(
                interaction.user.id
            ),
        )


# =========================================================
# PERSONAL STATS
# =========================================================

def winrate(
    wins: int,
    losses: int,
    draws: int,
) -> float:
    total = (
        wins
        + losses
        + draws
    )

    if total <= 0:
        return 0.0

    return (
        wins
        / total
    ) * 100


def stats_embed(
    user,
) -> discord.Embed:
    p = get_player(
        user.id
    )

    games = int(
        p.get(
            "games",
            0,
        )
    )

    wins = int(
        p.get(
            "wins",
            0,
        )
    )

    losses = int(
        p.get(
            "losses",
            0,
        )
    )

    draws = int(
        p.get(
            "draws",
            0,
        )
    )

    rate = winrate(
        wins,
        losses,
        draws,
    )

    embed = casino_embed(
        "📊 Meine Casino-Statistiken",
        (
            f"# 💰 {fmt(p['balance'])} EHRP Coins\n\n"
            f"🎮 Spiele: **{fmt(games)}**\n"
            f"✅ Siege: **{fmt(wins)}**\n"
            f"❌ Niederlagen: **{fmt(losses)}**\n"
            f"⚖️ Unentschieden: **{fmt(draws)}**\n"
            f"📊 Gewinnquote: **{rate:.1f}%**\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📈 Gesamt gewonnen: "
            f"**{fmt(p.get('total_won', 0))} Coins**\n"
            f"📉 Gesamt verloren: "
            f"**{fmt(p.get('total_lost', 0))} Coins**\n"
            f"💎 Größter Gewinn: "
            f"**{fmt(p.get('biggest_win', 0))} Coins**"
        ),
        user,
    )

    return embed


def game_stats_embed(
    user,
) -> discord.Embed:
    p = get_player(
        user.id
    )

    all_stats = p.get(
        "game_stats",
        {},
    )

    lines = []

    for key, label in GAME_LABELS.items():
        stats = all_stats.get(
            key,
            {},
        )

        games = int(
            stats.get(
                "games",
                0,
            )
        )

        wins = int(
            stats.get(
                "wins",
                0,
            )
        )

        losses = int(
            stats.get(
                "losses",
                0,
            )
        )

        draws = int(
            stats.get(
                "draws",
                0,
            )
        )

        rate = winrate(
            wins,
            losses,
            draws,
        )

        lines.append(
            f"### {label}\n"
            f"🎮 **{fmt(games)}** Spiele • "
            f"✅ **{fmt(wins)}** • "
            f"❌ **{fmt(losses)}** • "
            f"📊 **{rate:.0f}%**"
        )

    return casino_embed(
        "🎮 Meine Spielstatistiken",
        "\n\n".join(
            lines
        ),
        user,
    )


# =========================================================
# LEADERBOARD
# =========================================================

def leaderboard_embed(
    guild: discord.Guild,
) -> discord.Embed:
    ranking = sorted(
        casino_data.items(),
        key=lambda item: int(
            item[1].get(
                "balance",
                0,
            )
        ),
        reverse=True,
    )[:10]

    if not ranking:
        text = (
            "Noch keine Casino-Spieler vorhanden."
        )

    else:
        lines = []
        medals = [
            "🥇",
            "🥈",
            "🥉",
        ]

        for index, (
            uid,
            pdata,
        ) in enumerate(
            ranking,
            start=1,
        ):
            try:
                member = guild.get_member(
                    int(uid)
                )
            except ValueError:
                member = None

            if member:
                name = (
                    member.display_name
                )
            else:
                name = (
                    f"User {uid}"
                )

            if index <= 3:
                prefix = medals[
                    index - 1
                ]
            else:
                prefix = (
                    f"`#{index}`"
                )

            lines.append(
                f"{prefix} **{name}** — "
                f"**{fmt(pdata.get('balance', 0))} Coins**"
            )

        text = "\n".join(
            lines
        )

    return casino_embed(
        "🏆 EHRP Casino • Top 10",
        text,
    )


# =========================================================
# DAILY
# =========================================================

async def claim_daily(
    interaction: discord.Interaction,
):
    async with get_lock(
        interaction.user.id
    ):
        p = get_player(
            interaction.user.id
        )

        now = datetime.now(
            timezone.utc
        )

        last_raw = p.get(
            "daily"
        )

        if last_raw:
            try:
                last = datetime.fromisoformat(
                    last_raw
                )

                if (
                    last.tzinfo
                    is None
                ):
                    last = last.replace(
                        tzinfo=timezone.utc
                    )

                next_daily = (
                    last
                    + timedelta(
                        hours=24
                    )
                )

                if now < next_daily:
                    remaining = (
                        next_daily
                        - now
                    )

                    total_minutes = max(
                        1,
                        int(
                            remaining.total_seconds()
                            // 60
                        ),
                    )

                    hours, minutes = divmod(
                        total_minutes,
                        60,
                    )

                    return await respond_ephemeral(
                        interaction,
                        embed=casino_embed(
                            "⏳ Daily Bonus",
                            (
                                "Bereits abgeholt.\n\n"
                                f"⏱️ Wieder verfügbar in "
                                f"**{hours} Std. {minutes} Min.**"
                            ),
                            interaction.user,
                        ),
                    )

            except (
                ValueError,
                TypeError,
            ):
                pass

        p["balance"] += (
            DAILY_REWARD
        )

        p["daily"] = (
            now.isoformat()
        )

        save_data(
            casino_data
        )

    await respond_ephemeral(
        interaction,
        embed=casino_embed(
            "🎁 Daily Bonus",
            (
                f"**+{fmt(DAILY_REWARD)} EHRP Coins** "
                f"wurden gutgeschrieben.\n\n"
                f"💰 Guthaben: "
                f"**{fmt(p['balance'])} Coins**"
            ),
            interaction.user,
        ),
    )


# =========================================================
# PERSONAL CASINO
# =========================================================

def personal_casino_embed(
    user,
) -> discord.Embed:
    p = get_player(
        user.id
    )

    return casino_embed(
        "🎰 EHRP/VC • PRIVATE CASINO",
        (
            f"# Willkommen, {user.display_name}\n\n"
            f"💰 Guthaben: "
            f"**{fmt(p['balance'])} EHRP Coins**\n"
            f"🎮 Gespielte Runden: "
            f"**{fmt(p.get('games', 0))}**\n"
            f"🏆 Siege: "
            f"**{fmt(p.get('wins', 0))}**\n"
            f"💎 Größter Gewinn: "
            f"**{fmt(p.get('biggest_win', 0))} Coins**\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎰 Slots • 🃏 Blackjack • 🎡 Roulette\n"
            f"🪙 Coinflip • 🎲 Dice • 👑 Baccarat\n"
            f"⬆️⬇️ High / Low • 💣 Mines • 🚀 Crash\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Wählen Sie unten Ihren Einsatz und anschließend "
            f"direkt das gewünschte Spiel."
        ),
        user,
    )


class PersonalBetSelect(
    discord.ui.Select
):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"{fmt(bet)} Coins",
                value=str(bet),
                emoji="💰",
            )
            for bet in BET_OPTIONS
        ]

        options.append(
            discord.SelectOption(
                label="ALLES REIN",
                value="all",
                emoji="🔥",
            )
        )

        super().__init__(
            placeholder="💰 Einsatz festlegen",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        view = self.view

        if not isinstance(
            view,
            PersonalCasinoView,
        ):
            return

        if (
            interaction.user.id
            != view.owner_id
        ):
            return await respond_ephemeral(
                interaction,
                content="❌ Dieses Casino gehört nicht Ihnen.",
            )

        selected = self.values[0]

        view.selected_bet = selected

        if selected == "all":
            amount = get_player(
                interaction.user.id
            )["balance"]

            text = (
                f"🔥 **ALLES REIN** gewählt: "
                f"**{fmt(amount)} Coins**"
            )

        else:
            text = (
                f"💰 Einsatz gewählt: "
                f"**{fmt(int(selected))} Coins**"
            )

        await respond_ephemeral(
            interaction,
            content=text,
        )


class GameSelect(
    discord.ui.Select
):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Slots",
                value="slots",
                emoji="🎰",
                description="Walzen drehen und Multiplikatoren treffen.",
            ),
            discord.SelectOption(
                label="Blackjack",
                value="blackjack",
                emoji="🃏",
                description="Schlagen Sie den Dealer.",
            ),
            discord.SelectOption(
                label="Roulette",
                value="roulette",
                emoji="🎡",
                description="Rot, Schwarz, Gerade, Ungerade oder 0.",
            ),
            discord.SelectOption(
                label="Coinflip",
                value="coinflip",
                emoji="🪙",
                description="Kopf oder Zahl.",
            ),
            discord.SelectOption(
                label="Dice",
                value="dice",
                emoji="🎲",
                description="Ihr Würfel gegen das Casino.",
            ),
            discord.SelectOption(
                label="Baccarat",
                value="baccarat",
                emoji="👑",
                description="Spieler, Bank oder Unentschieden.",
            ),
            discord.SelectOption(
                label="High / Low",
                value="highlow",
                emoji="⬆️",
                description="Ist die nächste Karte höher oder niedriger?",
            ),
            discord.SelectOption(
                label="Mines",
                value="mines",
                emoji="💣",
                description="Felder öffnen und rechtzeitig auszahlen.",
            ),
            discord.SelectOption(
                label="Crash",
                value="crash",
                emoji="🚀",
                description="Steigen Sie vor dem Crash aus.",
            ),
        ]

        super().__init__(
            placeholder="🎮 Spiel auswählen und direkt starten",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        view = self.view

        if not isinstance(
            view,
            PersonalCasinoView,
        ):
            return

        if (
            interaction.user.id
            != view.owner_id
        ):
            return await respond_ephemeral(
                interaction,
                content="❌ Dieses Casino gehört nicht Ihnen.",
            )

        game = self.values[0]

        bet = resolve_bet(
            interaction.user.id,
            view.selected_bet,
        )

        if bet <= 0:
            return await respond_ephemeral(
                interaction,
                content="❌ Sie haben keine EHRP Coins.",
            )

        if game == "slots":
            await play_slots(
                interaction,
                bet,
            )

        elif game == "blackjack":
            await start_blackjack(
                interaction,
                bet,
            )

        elif game == "roulette":
            await start_roulette(
                interaction,
                bet,
            )

        elif game == "coinflip":
            await start_coinflip(
                interaction,
                bet,
            )

        elif game == "dice":
            await play_dice(
                interaction,
                bet,
            )

        elif game == "baccarat":
            await start_baccarat(
                interaction,
                bet,
            )

        elif game == "highlow":
            await start_highlow(
                interaction,
                bet,
            )

        elif game == "mines":
            await start_mines(
                interaction,
                bet,
            )

        elif game == "crash":
            await start_crash(
                interaction,
                bet,
            )


class PersonalCasinoView(
    discord.ui.View
):
    def __init__(
        self,
        owner_id: int,
    ):
        super().__init__(
            timeout=900
        )

        self.owner_id = owner_id
        self.selected_bet: int | str = 100

        self.add_item(
            PersonalBetSelect()
        )

        self.add_item(
            GameSelect()
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if (
            interaction.user.id
            != self.owner_id
        ):
            await respond_ephemeral(
                interaction,
                content="❌ Dieses persönliche Casino gehört nicht Ihnen.",
            )

            return False

        return True

    @discord.ui.button(
        label="Meine Statistiken",
        emoji="📊",
        style=discord.ButtonStyle.primary,
        row=2,
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await respond_ephemeral(
            interaction,
            embed=stats_embed(
                interaction.user
            ),
            view=StatsView(
                interaction.user.id
            ),
        )

    @discord.ui.button(
        label="Daily Bonus",
        emoji="🎁",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def daily(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await claim_daily(
            interaction
        )

    @discord.ui.button(
        label="Leaderboard",
        emoji="🏆",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if interaction.guild is None:
            return await respond_ephemeral(
                interaction,
                content="❌ Nur auf dem Server verfügbar.",
            )

        await respond_ephemeral(
            interaction,
            embed=leaderboard_embed(
                interaction.guild
            ),
        )
# =========================================================
# STATS VIEW
# =========================================================

class StatsView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await respond_ephemeral(
                interaction,
                content="❌ Diese Statistiken gehören nicht Ihnen.",
            )
            return False

        return True

    @discord.ui.button(
        label="Spielstatistiken",
        emoji="🎮",
        style=discord.ButtonStyle.primary,
    )
    async def game_stats(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            embed=game_stats_embed(
                interaction.user
            ),
            view=self,
        )

    @discord.ui.button(
        label="Gesamtübersicht",
        emoji="📊",
        style=discord.ButtonStyle.secondary,
    )
    async def total_stats(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            embed=stats_embed(
                interaction.user
            ),
            view=self,
        )

    @discord.ui.button(
        label="Casino öffnen",
        emoji="🎰",
        style=discord.ButtonStyle.success,
    )
    async def casino(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            embed=personal_casino_embed(
                interaction.user
            ),
            view=PersonalCasinoView(
                interaction.user.id
            ),
        )


# =========================================================
# PUBLIC CASINO PANEL
# =========================================================

def main_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎰 EHRP/VC • CASINO",
        description=(
            "## Willkommen im EHRP Casino\n"
            "Betreten Sie die exklusive Welt des "
            "**EHRP/VC Casinos**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎰 **Slots**\n"
            "🃏 **Blackjack**\n"
            "🎡 **Roulette**\n"
            "🪙 **Coinflip**\n"
            "🎲 **Dice**\n"
            "👑 **Baccarat**\n"
            "⬆️⬇️ **High / Low**\n"
            "💣 **Mines**\n"
            "🚀 **Crash**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 **Startguthaben:** "
            f"{fmt(START_BALANCE)} EHRP Coins\n"
            f"🎁 **Daily Bonus:** "
            f"{fmt(DAILY_REWARD)} EHRP Coins\n\n"
            "🎯 **Einsätze:** "
            "50 • 100 • 250 • 500 • 1K • 2.5K • 5K • 10K • "
            "**ALLES REIN**\n\n"
            "🏆 Leaderboard\n"
            "📊 Persönliche Statistiken\n"
            "🎮 Statistiken für jedes einzelne Spiel\n\n"
            "*Alle EHRP Coins sind rein virtuell und besitzen "
            "keinen Echtgeldwert.*"
        ),
        color=CASINO_COLOR,
    )

    embed.set_footer(
        text="EHRP/VC • Premium Casino System"
    )

    return embed


def entrance_embed(
    user,
) -> discord.Embed:
    return casino_embed(
        "🎡 EHRP/VC • CASINO",
        (
            "## Willkommen im Casino\n\n"
            "Das Roulette dreht sich...\n\n"
            "### 🎡 ◉ ◉ ◉\n"
            "**Bitte einen Moment warten...**\n\n"
            "✨ Ihr persönliches Casino wird vorbereitet."
        ),
        user,
    )


class CasinoEntranceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Casino betreten",
        emoji="🎰",
        style=discord.ButtonStyle.success,
        custom_id="ehrp_casino:enter",
    )
    async def enter(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        get_player(
            interaction.user.id
        )

        await interaction.response.send_message(
            embed=entrance_embed(
                interaction.user
            ),
            ephemeral=True,
        )

        await asyncio.sleep(0.65)

        try:
            await interaction.edit_original_response(
                embed=casino_embed(
                    "🎡 EHRP/VC • CASINO",
                    (
                        "## Roulette dreht sich\n\n"
                        "# ◉ 🎡 ◉\n\n"
                        "✨ **Willkommen im EHRP Casino...**"
                    ),
                    interaction.user,
                )
            )
        except discord.HTTPException:
            return

        await asyncio.sleep(0.65)

        try:
            await interaction.edit_original_response(
                embed=casino_embed(
                    "🎡 EHRP/VC • CASINO",
                    (
                        "## Roulette dreht sich\n\n"
                        "# 🎡 ◉ 🎡\n\n"
                        "💎 **Ihr Casino wird geöffnet...**"
                    ),
                    interaction.user,
                )
            )
        except discord.HTTPException:
            return

        await asyncio.sleep(0.65)

        try:
            await interaction.edit_original_response(
                embed=personal_casino_embed(
                    interaction.user
                ),
                view=PersonalCasinoView(
                    interaction.user.id
                ),
            )
        except discord.HTTPException:
            pass


# =========================================================
# ADMIN / PERMISSIONS
# =========================================================

def is_casino_admin(
    interaction: discord.Interaction,
) -> bool:
    if interaction.user.id == OWNER_USER_ID:
        return True

    if isinstance(
        interaction.user,
        discord.Member,
    ):
        return (
            interaction.user.guild_permissions.administrator
        )

    return False


# =========================================================
# COG
# =========================================================

class Casino(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    async def cog_load(self):
        # Das öffentliche Casino-Eingangspanel bleibt
        # auch nach einem Bot-Neustart funktionsfähig.
        self.bot.add_view(
            CasinoEntranceView()
        )

    # =====================================================
    # CASINO PANEL
    # =====================================================

    @app_commands.command(
        name="casino_panel",
        description="Erstellt das permanente EHRP/VC Casino-Panel.",
    )
    async def casino_panel(
        self,
        interaction: discord.Interaction,
    ):
        if not is_casino_admin(
            interaction
        ):
            return await respond_ephemeral(
                interaction,
                content="❌ Keine Berechtigung.",
            )

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):
            return await respond_ephemeral(
                interaction,
                content=(
                    "❌ Das Casino-Panel kann nur "
                    "in einem Textkanal erstellt werden."
                ),
            )

        await interaction.response.defer(
            ephemeral=True
        )

        embed = main_panel_embed()
        view = CasinoEntranceView()

        try:
            if CASINO_INTRO.exists():
                file = discord.File(
                    CASINO_INTRO,
                    filename="ehrp_casino_intro.gif",
                )

                embed.set_image(
                    url="attachment://ehrp_casino_intro.gif"
                )

                await interaction.channel.send(
                    file=file,
                    embed=embed,
                    view=view,
                )

            else:
                await interaction.channel.send(
                    embed=embed,
                    view=view,
                )

        except discord.HTTPException as error:
            return await interaction.followup.send(
                (
                    "❌ Das Casino-Panel konnte nicht "
                    f"erstellt werden.\n`{error}`"
                ),
                ephemeral=True,
            )

        await interaction.followup.send(
            (
                "✅ Das permanente **EHRP/VC Casino** "
                "wurde erfolgreich erstellt."
            ),
            ephemeral=True,
        )

    # =====================================================
    # CASINO STATUS
    # =====================================================

    @app_commands.command(
        name="casino_status",
        description="Zeigt den Status des Casino-Systems.",
    )
    async def casino_status(
        self,
        interaction: discord.Interaction,
    ):
        total_coins = sum(
            int(
                player.get(
                    "balance",
                    0,
                )
            )
            for player in casino_data.values()
            if isinstance(
                player,
                dict,
            )
        )

        total_games = sum(
            int(
                player.get(
                    "games",
                    0,
                )
            )
            for player in casino_data.values()
            if isinstance(
                player,
                dict,
            )
        )

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "🎰 EHRP Casino • Systemstatus",
                (
                    "🟢 **Casino online**\n\n"
                    f"👥 Registrierte Spieler: "
                    f"**{fmt(len(casino_data))}**\n"
                    f"🎮 Gespielte Runden: "
                    f"**{fmt(total_games)}**\n"
                    f"💰 Coins im Umlauf: "
                    f"**{fmt(total_coins)}**\n\n"
                    f"💵 Startguthaben: "
                    f"**{fmt(START_BALANCE)} Coins**\n"
                    f"🎁 Daily Bonus: "
                    f"**{fmt(DAILY_REWARD)} Coins**\n\n"
                    f"💾 Datendatei:\n"
                    f"`{DATA_FILE}`\n\n"
                    f"🎬 Casino Intro: "
                    f"**{'gefunden' if CASINO_INTRO.exists() else 'nicht gefunden'}**"
                ),
            ),
        )

    # =====================================================
    # PERSONAL CASINO COMMAND
    # =====================================================

    @app_commands.command(
        name="casino",
        description="Öffnet Ihr persönliches EHRP Casino.",
    )
    async def casino(
        self,
        interaction: discord.Interaction,
    ):
        get_player(
            interaction.user.id
        )

        await respond_ephemeral(
            interaction,
            embed=personal_casino_embed(
                interaction.user
            ),
            view=PersonalCasinoView(
                interaction.user.id
            ),
        )

    # =====================================================
    # CASINO STATS COMMAND
    # =====================================================

    @app_commands.command(
        name="casino_stats",
        description="Zeigt Ihre persönlichen Casino-Statistiken.",
    )
    async def casino_stats(
        self,
        interaction: discord.Interaction,
    ):
        await respond_ephemeral(
            interaction,
            embed=stats_embed(
                interaction.user
            ),
            view=StatsView(
                interaction.user.id
            ),
        )

    # =====================================================
    # CASINO COINS ADMIN
    # =====================================================

    @app_commands.command(
        name="casino_coins",
        description="Verwaltet EHRP Coins eines Mitglieds.",
    )
    @app_commands.describe(
        mitglied="Mitglied",
        aktion="Coins setzen, hinzufügen oder entfernen",
        betrag="Anzahl der EHRP Coins",
    )
    @app_commands.choices(
        aktion=[
            app_commands.Choice(
                name="Setzen",
                value="set",
            ),
            app_commands.Choice(
                name="Hinzufügen",
                value="add",
            ),
            app_commands.Choice(
                name="Entfernen",
                value="remove",
            ),
        ]
    )
    async def casino_coins(
        self,
        interaction: discord.Interaction,
        mitglied: discord.Member,
        aktion: app_commands.Choice[str],
        betrag: app_commands.Range[
            int,
            0,
            100_000_000,
        ],
    ):
        if not is_casino_admin(
            interaction
        ):
            return await respond_ephemeral(
                interaction,
                content="❌ Keine Berechtigung.",
            )

        async with get_lock(
            mitglied.id
        ):
            p = get_player(
                mitglied.id
            )

            old_balance = int(
                p["balance"]
            )

            if aktion.value == "set":
                p["balance"] = int(
                    betrag
                )

            elif aktion.value == "add":
                p["balance"] += int(
                    betrag
                )

            elif aktion.value == "remove":
                p["balance"] = max(
                    0,
                    int(
                        p["balance"]
                    )
                    - int(
                        betrag
                    ),
                )

            new_balance = int(
                p["balance"]
            )

            save_data(
                casino_data
            )

        await respond_ephemeral(
            interaction,
            embed=casino_embed(
                "💰 Casino Coins aktualisiert",
                (
                    f"👤 Mitglied: {mitglied.mention}\n"
                    f"🛠️ Aktion: **{aktion.name}**\n"
                    f"💵 Betrag: **{fmt(betrag)} Coins**\n\n"
                    f"Vorher: **{fmt(old_balance)} Coins**\n"
                    f"Nachher: **{fmt(new_balance)} Coins**"
                ),
                interaction.user,
            ),
        )

        await casino_log(
            interaction.guild,
            "🛠️ Casino Administration",
            (
                f"{interaction.user.mention} änderte "
                f"Coins von {mitglied.mention}\n"
                f"Aktion: **{aktion.name}**\n"
                f"Betrag: **{fmt(betrag)}**\n"
                f"Vorher: **{fmt(old_balance)}**\n"
                f"Neu: **{fmt(new_balance)}**"
            ),
        )

    # =====================================================
    # BACKUP COMMAND
    # =====================================================

    @app_commands.command(
        name="casino_backup",
        description="Erstellt ein Backup der Casino-Spielerdaten.",
    )
    async def casino_backup(
        self,
        interaction: discord.Interaction,
    ):
        if not is_casino_admin(
            interaction
        ):
            return await respond_ephemeral(
                interaction,
                content="❌ Keine Berechtigung.",
            )

        save_data(
            casino_data
        )

        if not DATA_FILE.exists():
            return await respond_ephemeral(
                interaction,
                content="❌ Keine Casino-Datendatei gefunden.",
            )

        await interaction.response.defer(
            ephemeral=True
        )

        backup_name = (
            "ehrp_casino_backup_"
            + datetime.now(
                timezone.utc
            ).strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            + ".json"
        )

        try:
            await interaction.followup.send(
                content=(
                    "💾 **Casino Backup erstellt**\n\n"
                    f"👥 Spieler: **{fmt(len(casino_data))}**\n"
                    "⚠️ Bewahren Sie diese Datei sicher auf."
                ),
                file=discord.File(
                    DATA_FILE,
                    filename=backup_name,
                ),
                ephemeral=True,
            )

        except discord.HTTPException as error:
            await interaction.followup.send(
                (
                    "❌ Backup konnte nicht gesendet werden.\n"
                    f"`{error}`"
                ),
                ephemeral=True,
            )


# =========================================================
# SETUP
# =========================================================

async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        Casino(bot)
    )


# =========================================================
# TEIL 6 / 6
# ABSCHLUSS / STARTUP-SICHERHEIT
# =========================================================

# Dieser letzte Teil ergänzt keine neuen Spiele mehr.
# Er sorgt dafür, dass bestehende Daten nach dem Upgrade
# automatisch ergänzt und NICHT zurückgesetzt werden.


def migrate_all_players():
    """
    Ergänzt bei bereits vorhandenen Spielern ausschließlich
    fehlende Felder.

    Vorhandene Werte wie:
    - balance
    - daily
    - games
    - wins
    - losses
    - draws
    - total_won
    - total_lost
    - biggest_win

    werden NICHT überschrieben.
    """

    changed = False
    template = default_player()

    for uid, pdata in list(casino_data.items()):
        if not isinstance(pdata, dict):
            continue

        for key, default_value in template.items():
            if key not in pdata:
                pdata[key] = default_value
                changed = True

        if "game_stats" not in pdata:
            pdata["game_stats"] = {}
            changed = True

        for game_key in GAME_LABELS:
            if game_key not in pdata["game_stats"]:
                pdata["game_stats"][game_key] = {
                    "games": 0,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "won": 0,
                    "lost": 0,
                    "biggest_win": 0,
                }
                changed = True

            else:
                stats = pdata["game_stats"][game_key]

                defaults = {
                    "games": 0,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "won": 0,
                    "lost": 0,
                    "biggest_win": 0,
                }

                for key, value in defaults.items():
                    if key not in stats:
                        stats[key] = value
                        changed = True

    if changed:
        save_data(casino_data)


# Migration direkt beim Laden durchführen.
migrate_all_players()
