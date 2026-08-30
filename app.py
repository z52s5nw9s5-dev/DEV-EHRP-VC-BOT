from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
import json
import os
import random
import threading
import tempfile


app = Flask(__name__)

DATA_DIR = Path(
    os.getenv("CASINO_DATA_DIR", "data")
)

DATA_FILE = DATA_DIR / "casino_data.json"

START_BALANCE = 1000

lock = threading.RLock()

# Laufende Blackjack-Runden
blackjack_sessions = {}


# =========================================================
# DATA
# =========================================================

def load():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            "{}",
            encoding="utf-8"
        )

    try:
        data = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            ) or "{}"
        )

        if isinstance(data, dict):
            return data

        return {}

    except Exception:
        return {}


def save(data):
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fd, name = tempfile.mkstemp(
        dir=DATA_DIR,
        suffix=".tmp"
    )

    os.close(fd)

    Path(name).write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    os.replace(
        name,
        DATA_FILE
    )


def player(data, uid):
    p = data.setdefault(
        str(uid),
        {}
    )

    defaults = {
        "balance": START_BALANCE,
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "total_won": 0,
        "total_lost": 0,
        "biggest_win": 0
    }

    for key, value in defaults.items():
        p.setdefault(
            key,
            value
        )

    return p


# =========================================================
# PLAYER STATS
# =========================================================

def finish_game(
    p,
    profit,
    win=False,
    draw=False
):
    p["balance"] += profit
    p["games"] += 1

    if draw:
        p["draws"] += 1

    elif win:
        p["wins"] += 1

        p["total_won"] += max(
            0,
            profit
        )

        p["biggest_win"] = max(
            p["biggest_win"],
            profit
        )

    else:
        p["losses"] += 1

        p["total_lost"] += abs(
            profit
        )


# =========================================================
# ROUTES
# =========================================================

@app.get("/")
def home():
    return render_template(
        "casino.html"
    )


@app.get("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(
        "assets",
        filename
    )


@app.get("/api/player/<uid>")
def get_player(uid):
    with lock:
        data = load()

        p = player(
            data,
            uid
        )

        save(data)

        return jsonify(p)


# =========================================================
# CARDS
# =========================================================

SUITS = [
    "♠",
    "♥",
    "♦",
    "♣"
]

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
    "K"
]


def create_deck():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append({
                "rank": rank,
                "suit": suit
            })

    random.shuffle(deck)

    return deck


def card_value(card):
    rank = card["rank"]

    if rank in [
        "J",
        "Q",
        "K"
    ]:
        return 10

    if rank == "A":
        return 11

    return int(rank)


def hand_value(hand):
    total = sum(
        card_value(card)
        for card in hand
    )

    aces = sum(
        1
        for card in hand
        if card["rank"] == "A"
    )

    while (
        total > 21
        and aces > 0
    ):
        total -= 10
        aces -= 1

    return total


def is_blackjack(hand):
    return (
        len(hand) == 2
        and hand_value(hand) == 21
    )


# =========================================================
# BLACKJACK START
# =========================================================

@app.post("/api/blackjack/start")
def blackjack_start():
    body = request.get_json(
        force=True
    )

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    bet = body.get(
        "bet",
        100
    )

    with lock:
        data = load()

        p = player(
            data,
            uid
        )

        if bet == "all":
            bet = p["balance"]

        else:
            try:
                bet = int(bet)

            except Exception:
                bet = 100

        if bet <= 0:
            return jsonify({
                "ok": False,
                "error": "Ungültiger Einsatz."
            }), 400

        if p["balance"] < bet:
            return jsonify({
                "ok": False,
                "error": "Nicht genügend Coins.",
                "player": p
            }), 400

        deck = create_deck()

        player_hand = [
            deck.pop(),
            deck.pop()
        ]

        dealer_hand = [
            deck.pop(),
            deck.pop()
        ]

        blackjack_sessions[uid] = {
            "deck": deck,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "bet": bet
        }

        player_blackjack = is_blackjack(
            player_hand
        )

        dealer_blackjack = is_blackjack(
            dealer_hand
        )

        # Sofortiges Ergebnis
        if (
            player_blackjack
            or dealer_blackjack
        ):
            session = blackjack_sessions.pop(
                uid
            )

            if (
                player_blackjack
                and dealer_blackjack
            ):
                profit = 0

                finish_game(
                    p,
                    profit,
                    draw=True
                )

                result = "push"

            elif player_blackjack:
                # Blackjack zahlt 3:2
                profit = int(
                    bet * 1.5
                )

                finish_game(
                    p,
                    profit,
                    win=True
                )

                result = "blackjack"

            else:
                profit = -bet

                finish_game(
                    p,
                    profit
                )

                result = "dealer_blackjack"

            save(data)

            return jsonify({
                "ok": True,
                "finished": True,
                "result": result,
                "profit": profit,
                "player_hand": player_hand,
                "dealer_hand": dealer_hand,
                "player_value": hand_value(
                    player_hand
                ),
                "dealer_value": hand_value(
                    dealer_hand
                ),
                "player": p
            })

        save(data)

        return jsonify({
            "ok": True,
            "finished": False,
            "player_hand": player_hand,

            # Zweite Dealerkarte bleibt verdeckt
            "dealer_hand": [
                dealer_hand[0],
                {
                    "rank": "?",
                    "suit": "?"
                }
            ],

            "player_value": hand_value(
                player_hand
            ),

            "dealer_value": card_value(
                dealer_hand[0]
            ),

            "player": p
        })


# =========================================================
# BLACKJACK HIT
# =========================================================

@app.post("/api/blackjack/hit")
def blackjack_hit():
    body = request.get_json(
        force=True
    )

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:
        session = blackjack_sessions.get(
            uid
        )

        if not session:
            return jsonify({
                "ok": False,
                "error": "Keine aktive Blackjack-Runde."
            }), 400

        session["player_hand"].append(
            session["deck"].pop()
        )

        value = hand_value(
            session["player_hand"]
        )

        if value > 21:
            data = load()

            p = player(
                data,
                uid
            )

            bet = session["bet"]

            profit = -bet

            finish_game(
                p,
                profit
            )

            blackjack_sessions.pop(
                uid,
                None
            )

            save(data)

            return jsonify({
                "ok": True,
                "finished": True,
                "result": "bust",
                "profit": profit,
                "player_hand":
                    session["player_hand"],
                "dealer_hand":
                    session["dealer_hand"],
                "player_value":
                    value,
                "dealer_value":
                    hand_value(
                        session[
                            "dealer_hand"
                        ]
                    ),
                "player": p
            })

        return jsonify({
            "ok": True,
            "finished": False,
            "player_hand":
                session["player_hand"],

            "dealer_hand": [
                session[
                    "dealer_hand"
                ][0],
                {
                    "rank": "?",
                    "suit": "?"
                }
            ],

            "player_value":
                value,

            "dealer_value":
                card_value(
                    session[
                        "dealer_hand"
                    ][0]
                )
        })


# =========================================================
# BLACKJACK STAND
# =========================================================

@app.post("/api/blackjack/stand")
def blackjack_stand():
    body = request.get_json(
        force=True
    )

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:
        session = blackjack_sessions.get(
            uid
        )

        if not session:
            return jsonify({
                "ok": False,
                "error": "Keine aktive Blackjack-Runde."
            }), 400

        player_hand = session[
            "player_hand"
        ]

        dealer_hand = session[
            "dealer_hand"
        ]

        deck = session[
            "deck"
        ]

        bet = session[
            "bet"
        ]

        # Dealer zieht bis mindestens 17
        while (
            hand_value(
                dealer_hand
            ) < 17
        ):
            dealer_hand.append(
                deck.pop()
            )

        player_total = hand_value(
            player_hand
        )

        dealer_total = hand_value(
            dealer_hand
        )

        data = load()

        p = player(
            data,
            uid
        )

        if dealer_total > 21:
            profit = bet
            result = "dealer_bust"
            win = True
            draw = False

        elif player_total > dealer_total:
            profit = bet
            result = "win"
            win = True
            draw = False

        elif player_total < dealer_total:
            profit = -bet
            result = "lose"
            win = False
            draw = False

        else:
            profit = 0
            result = "push"
            win = False
            draw = True

        finish_game(
            p,
            profit,
            win=win,
            draw=draw
        )

        blackjack_sessions.pop(
            uid,
            None
        )

        save(data)

        return jsonify({
            "ok": True,
            "finished": True,
            "result": result,
            "profit": profit,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "player_value": player_total,
            "dealer_value": dealer_total,
            "player": p
        })


# =========================================================
# NORMAL CASINO GAMES
# =========================================================

@app.post("/api/play")
def play():
    body = request.get_json(
        force=True
    )

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    game = str(
        body.get(
            "game",
            "slots"
        )
    )

    bet = body.get(
        "bet",
        100
    )

    with lock:
        data = load()

        p = player(
            data,
            uid
        )

        if bet == "all":
            bet = p["balance"]

        else:
            try:
                bet = int(bet)

            except Exception:
                return jsonify({
                    "ok": False,
                    "error": "Ungültiger Einsatz."
                }), 400

        if (
            bet <= 0
            or p["balance"] < bet
        ):
            return jsonify({
                "ok": False,
                "error": "Nicht genügend Coins",
                "player": p
            }), 400

        win = False
        draw = False
        profit = 0
        detail = {}


        # =================================================
        # SLOTS
        # =================================================

        if game == "slots":
            symbols = [
                "🍒",
                "🍋",
                "🔔",
                "👑",
                "💎",
                "7️⃣"
            ]

            reels = [
                random.choice(symbols)
                for _ in range(3)
            ]

            detail = {
                "reels": reels
            }

            if len(set(reels)) == 1:
                multiplier = {
                    "7️⃣": 10,
                    "💎": 8,
                    "👑": 6,
                    "🔔": 4,
                    "🍒": 3,
                    "🍋": 3
                }[reels[0]]

                profit = bet * (
                    multiplier - 1
                )

                win = True

            elif len(set(reels)) == 2:
                profit = bet // 2
                win = True

            else:
                profit = -bet


        # =================================================
        # DICE
        # =================================================

        elif game == "dice":
            you = random.randint(
                1,
                6
            )

            casino = random.randint(
                1,
                6
            )

            detail = {
                "you": you,
                "casino": casino
            }

            if you > casino:
                profit = bet
                win = True

            elif you == casino:
                profit = 0
                draw = True

            else:
                profit = -bet


        # =================================================
        # COINFLIP
        # =================================================

        elif game == "coinflip":
            choice = body.get(
                "choice",
                "Kopf"
            )

            result = random.choice([
                "Kopf",
                "Zahl"
            ])

            detail = {
                "choice": choice,
                "result": result
            }

            if choice == result:
                profit = bet
                win = True

            else:
                profit = -bet


        # =================================================
        # ROULETTE
        # =================================================

        elif game == "roulette":
            choice = body.get(
                "choice",
                "red"
            )

            number = random.randint(
                0,
                36
            )

            reds = {
                1, 3, 5, 7, 9,
                12, 14, 16, 18,
                19, 21, 23, 25,
                27, 30, 32, 34, 36
            }

            if number == 0:
                color = "green"

            elif number in reds:
                color = "red"

            else:
                color = "black"

            detail = {
                "number": number,
                "color": color
            }

            if choice == color:
                win = True

                if choice == "green":
                    profit = bet * 35

                else:
                    profit = bet

            else:
                profit = -bet


        # =================================================
        # TEMP OTHER GAMES
        # =================================================

        else:
            roll = random.random()

            detail = {
                "roll": round(
                    roll,
                    3
                )
            }

            if roll > 0.52:
                profit = bet
                win = True

            else:
                profit = -bet


        finish_game(
            p,
            profit,
            win=win,
            draw=draw
        )

        save(data)

        return jsonify({
            "ok": True,
            "profit": profit,
            "detail": detail,
            "player": p
        })


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "10000"
            )
        )
    )
