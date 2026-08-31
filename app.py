from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
import json
import os
import random
import threading
import tempfile


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR = Path(
    os.getenv(
        "CASINO_DATA_DIR",
        str(BASE_DIR / "data")
    )
)

DATA_FILE = DATA_DIR / "casino_data.json"

START_BALANCE = 1000

lock = threading.RLock()

blackjack_sessions = {}
highlow_sessions = {}
mines_sessions = {}
crash_sessions = {}


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

    except Exception:
        pass

    return {}


def save(data):

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fd, temp_name = tempfile.mkstemp(
        dir=DATA_DIR,
        suffix=".tmp"
    )

    os.close(fd)

    temp_path = Path(temp_name)

    try:

        temp_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        os.replace(
            temp_path,
            DATA_FILE
        )

    finally:

        if temp_path.exists():

            try:
                temp_path.unlink()

            except Exception:
                pass


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


def parse_bet(raw_bet, balance):

    if raw_bet == "all":
        return int(balance)

    try:
        bet = int(raw_bet)

    except Exception:
        raise ValueError(
            "Ungültiger Einsatz."
        )

    if bet <= 0:
        raise ValueError(
            "Ungültiger Einsatz."
        )

    if bet > balance:
        raise ValueError(
            "Nicht genügend Coins."
        )

    return bet


def finish_game(
    p,
    profit,
    win=False,
    draw=False
):

    p["balance"] += int(profit)
    p["games"] += 1

    if draw:

        p["draws"] += 1

    elif win:

        p["wins"] += 1

        p["total_won"] += max(
            0,
            int(profit)
        )

        p["biggest_win"] = max(
            p["biggest_win"],
            int(profit)
        )

    else:

        p["losses"] += 1

        p["total_lost"] += abs(
            min(
                0,
                int(profit)
            )
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
        ASSETS_DIR,
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

    if rank in (
        "J",
        "Q",
        "K"
    ):
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

    while total > 21 and aces:

        total -= 10
        aces -= 1

    return total


def is_blackjack(hand):

    return (
        len(hand) == 2
        and hand_value(hand) == 21
    )


def highlow_value(card):

    values = {
        "A": 1,
        "J": 11,
        "Q": 12,
        "K": 13
    }

    rank = card["rank"]

    if rank in values:
        return values[rank]

    return int(rank)


# =========================================================
# BLACKJACK START
# =========================================================

@app.post("/api/blackjack/start")
def blackjack_start():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error),
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

        player_bj = is_blackjack(
            player_hand
        )

        dealer_bj = is_blackjack(
            dealer_hand
        )

        if player_bj or dealer_bj:

            blackjack_sessions.pop(
                uid,
                None
            )

            if player_bj and dealer_bj:

                profit = 0
                result = "push"

                finish_game(
                    p,
                    0,
                    draw=True
                )

            elif player_bj:

                profit = int(
                    bet * 1.5
                )

                result = "blackjack"

                finish_game(
                    p,
                    profit,
                    win=True
                )

            else:

                profit = -bet
                result = "dealer_blackjack"

                finish_game(
                    p,
                    profit
                )

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
        silent=True
    ) or {}

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

        if value <= 21:

            return jsonify({
                "ok": True,
                "finished": False,
                "player_hand":
                    session["player_hand"],
                "dealer_hand": [
                    session["dealer_hand"][0],
                    {
                        "rank": "?",
                        "suit": "?"
                    }
                ],
                "player_value": value,
                "dealer_value":
                    card_value(
                        session["dealer_hand"][0]
                    )
            })

        data = load()
        p = player(data, uid)

        profit = -session["bet"]

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
            "player_value": value,
            "dealer_value":
                hand_value(
                    session["dealer_hand"]
                ),
            "player": p
        })


# =========================================================
# BLACKJACK STAND
# =========================================================

@app.post("/api/blackjack/stand")
def blackjack_stand():

    body = request.get_json(
        silent=True
    ) or {}

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

        while (
            hand_value(dealer_hand) < 17
        ):

            dealer_hand.append(
                session["deck"].pop()
            )

        player_total = hand_value(
            player_hand
        )

        dealer_total = hand_value(
            dealer_hand
        )

        data = load()
        p = player(data, uid)

        bet = session["bet"]

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
# HIGH / LOW
# =========================================================

@app.post("/api/highlow/start")
def highlow_start():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error)
            }), 400

        deck = create_deck()

        first_card = deck.pop()

        highlow_sessions[uid] = {
            "deck": deck,
            "card": first_card,
            "bet": bet
        }

        return jsonify({
            "ok": True,
            "card": first_card,
            "value": highlow_value(
                first_card
            )
        })


@app.post("/api/highlow/guess")
def highlow_guess():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    guess = str(
        body.get(
            "guess",
            "higher"
        )
    )

    with lock:

        session = highlow_sessions.get(
            uid
        )

        if not session:

            return jsonify({
                "ok": False,
                "error": "Keine aktive High/Low-Runde."
            }), 400

        old_card = session["card"]
        new_card = session["deck"].pop()

        old_value = highlow_value(
            old_card
        )

        new_value = highlow_value(
            new_card
        )

        data = load()
        p = player(data, uid)

        bet = session["bet"]

        if old_value == new_value:

            profit = 0
            result = "draw"

            finish_game(
                p,
                0,
                draw=True
            )

        else:

            correct = (
                (
                    guess == "higher"
                    and new_value > old_value
                )
                or
                (
                    guess == "lower"
                    and new_value < old_value
                )
            )

            if correct:

                profit = bet
                result = "win"

                finish_game(
                    p,
                    profit,
                    win=True
                )

            else:

                profit = -bet
                result = "lose"

                finish_game(
                    p,
                    profit
                )

        highlow_sessions.pop(
            uid,
            None
        )

        save(data)

        return jsonify({
            "ok": True,
            "result": result,
            "profit": profit,
            "old_card": old_card,
            "new_card": new_card,
            "old_value": old_value,
            "new_value": new_value,
            "player": p
        })


# =========================================================
# BACCARAT
# =========================================================

def baccarat_card_value(card):

    rank = card["rank"]

    if rank in (
        "10",
        "J",
        "Q",
        "K"
    ):
        return 0

    if rank == "A":
        return 1

    return int(rank)


def baccarat_total(hand):

    return sum(
        baccarat_card_value(card)
        for card in hand
    ) % 10


@app.post("/api/baccarat/play")
def baccarat_play():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    choice = str(
        body.get(
            "choice",
            "player"
        )
    )

    if choice not in (
        "player",
        "banker",
        "tie"
    ):

        return jsonify({
            "ok": False,
            "error": "Ungültige Auswahl."
        }), 400

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error)
            }), 400

        deck = create_deck()

        player_hand = [
            deck.pop(),
            deck.pop()
        ]

        banker_hand = [
            deck.pop(),
            deck.pop()
        ]

        player_total = baccarat_total(
            player_hand
        )

        banker_total = baccarat_total(
            banker_hand
        )

        if (
            player_total not in (8, 9)
            and banker_total not in (8, 9)
        ):

            player_third = None

            if player_total <= 5:

                player_third = deck.pop()

                player_hand.append(
                    player_third
                )

            player_total = baccarat_total(
                player_hand
            )

            if player_third is None:

                if banker_total <= 5:

                    banker_hand.append(
                        deck.pop()
                    )

            else:

                third = baccarat_card_value(
                    player_third
                )

                draw_banker = (
                    banker_total <= 2
                    or
                    (
                        banker_total == 3
                        and third != 8
                    )
                    or
                    (
                        banker_total == 4
                        and third in (
                            2, 3, 4, 5, 6, 7
                        )
                    )
                    or
                    (
                        banker_total == 5
                        and third in (
                            4, 5, 6, 7
                        )
                    )
                    or
                    (
                        banker_total == 6
                        and third in (
                            6, 7
                        )
                    )
                )

                if draw_banker:

                    banker_hand.append(
                        deck.pop()
                    )

            banker_total = baccarat_total(
                banker_hand
            )

        if player_total > banker_total:

            winner = "player"

        elif banker_total > player_total:

            winner = "banker"

        else:

            winner = "tie"

        if choice == winner:

            if winner == "tie":

                profit = bet * 8

            elif winner == "banker":

                profit = int(
                    bet * 0.95
                )

            else:

                profit = bet

            finish_game(
                p,
                profit,
                win=True
            )

        else:

            # Player/Banker bets push when hand is a tie.
            if (
                winner == "tie"
                and choice in (
                    "player",
                    "banker"
                )
            ):

                profit = 0

                finish_game(
                    p,
                    0,
                    draw=True
                )

            else:

                profit = -bet

                finish_game(
                    p,
                    profit
                )

        save(data)

        return jsonify({
            "ok": True,
            "winner": winner,
            "profit": profit,
            "player_hand": player_hand,
            "banker_hand": banker_hand,
            "player_total": player_total,
            "banker_total": banker_total,
            "player": p
        })


# =========================================================
# MINES
# =========================================================

@app.post("/api/mines/start")
def mines_start():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error)
            }), 400

        mine_count = 4

        mines = set(
            random.sample(
                range(16),
                mine_count
            )
        )

        mines_sessions[uid] = {
            "bet": bet,
            "mines": mines,
            "opened": set(),
            "mine_count": mine_count
        }

        return jsonify({
            "ok": True,
            "size": 16,
            "mine_count": mine_count,
            "opened": [],
            "multiplier": 1.0
        })


@app.post("/api/mines/open")
def mines_open():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    try:

        cell = int(
            body.get("cell")
        )

    except Exception:

        return jsonify({
            "ok": False,
            "error": "Ungültiges Feld."
        }), 400

    with lock:

        session = mines_sessions.get(
            uid
        )

        if not session:

            return jsonify({
                "ok": False,
                "error": "Keine aktive Mines-Runde."
            }), 400

        if cell < 0 or cell >= 16:

            return jsonify({
                "ok": False,
                "error": "Ungültiges Feld."
            }), 400

        if cell in session["opened"]:

            return jsonify({
                "ok": False,
                "error": "Feld wurde bereits geöffnet."
            }), 400

        if cell in session["mines"]:

            data = load()
            p = player(data, uid)

            profit = -session["bet"]

            finish_game(
                p,
                profit
            )

            mines = sorted(
                session["mines"]
            )

            mines_sessions.pop(
                uid,
                None
            )

            save(data)

            return jsonify({
                "ok": True,
                "finished": True,
                "hit_mine": True,
                "profit": profit,
                "mines": mines,
                "player": p
            })

        session["opened"].add(
            cell
        )

        safe_total = (
            16 -
            session["mine_count"]
        )

        opened_count = len(
            session["opened"]
        )

        multiplier = round(
            1 + (
                opened_count
                * 0.22
            ),
            2
        )

        return jsonify({
            "ok": True,
            "finished": False,
            "hit_mine": False,
            "opened": sorted(
                session["opened"]
            ),
            "safe_total": safe_total,
            "multiplier": multiplier
        })


@app.post("/api/mines/cashout")
def mines_cashout():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        session = mines_sessions.get(
            uid
        )

        if not session:

            return jsonify({
                "ok": False,
                "error": "Keine aktive Mines-Runde."
            }), 400

        opened_count = len(
            session["opened"]
        )

        if opened_count == 0:

            return jsonify({
                "ok": False,
                "error": "Öffne zuerst mindestens ein Feld."
            }), 400

        multiplier = round(
            1 + (
                opened_count
                * 0.22
            ),
            2
        )

        profit = int(
            session["bet"]
            * (
                multiplier - 1
            )
        )

        data = load()
        p = player(data, uid)

        finish_game(
            p,
            profit,
            win=True
        )

        mines = sorted(
            session["mines"]
        )

        mines_sessions.pop(
            uid,
            None
        )

        save(data)

        return jsonify({
            "ok": True,
            "finished": True,
            "profit": profit,
            "multiplier": multiplier,
            "mines": mines,
            "player": p
        })


# =========================================================
# CRASH
# =========================================================

@app.post("/api/crash/start")
def crash_start():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error)
            }), 400

        # Server decides the crash point before the round.
        # Virtual/fun currency only.
        roll = random.random()

        crash_point = round(
            max(
                1.01,
                min(
                    20.0,
                    0.97 / max(
                        0.05,
                        1.0 - roll
                    )
                )
            ),
            2
        )

        crash_sessions[uid] = {
            "bet": bet,
            "crash_point": crash_point,
            "current": 1.0
        }

        return jsonify({
            "ok": True,
            "started": True,
            "multiplier": 1.0
        })


@app.post("/api/crash/tick")
def crash_tick():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        session = crash_sessions.get(
            uid
        )

        if not session:

            return jsonify({
                "ok": False,
                "error": "Keine aktive Crash-Runde."
            }), 400

        session["current"] = round(
            session["current"] + 0.08,
            2
        )

        if (
            session["current"]
            >= session["crash_point"]
        ):

            data = load()
            p = player(data, uid)

            profit = -session["bet"]

            finish_game(
                p,
                profit
            )

            crash_sessions.pop(
                uid,
                None
            )

            save(data)

            return jsonify({
                "ok": True,
                "crashed": True,
                "multiplier":
                    session["crash_point"],
                "profit": profit,
                "player": p
            })

        return jsonify({
            "ok": True,
            "crashed": False,
            "multiplier":
                session["current"]
        })


@app.post("/api/crash/cashout")
def crash_cashout():

    body = request.get_json(
        silent=True
    ) or {}

    uid = str(
        body.get(
            "user_id",
            "demo"
        )
    )

    with lock:

        session = crash_sessions.get(
            uid
        )

        if not session:

            return jsonify({
                "ok": False,
                "error": "Keine aktive Crash-Runde."
            }), 400

        multiplier = session[
            "current"
        ]

        profit = int(
            session["bet"]
            * (
                multiplier - 1
            )
        )

        data = load()
        p = player(data, uid)

        finish_game(
            p,
            profit,
            win=True
        )

        crash_sessions.pop(
            uid,
            None
        )

        save(data)

        return jsonify({
            "ok": True,
            "cashed_out": True,
            "multiplier": multiplier,
            "profit": profit,
            "player": p
        })


# =========================================================
# ORIGINAL QUICK GAMES
# =========================================================

@app.post("/api/play")
def play():

    body = request.get_json(
        silent=True
    ) or {}

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

    allowed_games = {
        "slots",
        "dice",
        "coinflip",
        "roulette"
    }

    if game not in allowed_games:

        return jsonify({
            "ok": False,
            "error":
                "Dieses Spiel benutzt eine eigene Game-Engine."
        }), 400

    with lock:

        data = load()
        p = player(data, uid)

        try:

            bet = parse_bet(
                body.get("bet", 100),
                p["balance"]
            )

        except ValueError as error:

            return jsonify({
                "ok": False,
                "error": str(error),
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

                profit = (
                    bet *
                    (multiplier - 1)
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

            if choice not in (
                "Kopf",
                "Zahl"
            ):

                return jsonify({
                    "ok": False,
                    "error": "Ungültige Auswahl."
                }), 400

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

            if choice not in (
                "red",
                "black",
                "green"
            ):

                return jsonify({
                    "ok": False,
                    "error": "Ungültige Auswahl."
                }), 400

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
        ),
        debug=False,
        use_reloader=False
    )
