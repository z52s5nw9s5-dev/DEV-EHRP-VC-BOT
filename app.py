import json
import os
import random
import secrets
import threading
from pathlib import Path

import requests
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)


# =========================================================
# APP
# =========================================================

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32),
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# =========================================================
# PATHS / DATA
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR = Path(
    os.getenv(
        "CASINO_DATA_DIR",
        str(BASE_DIR / "data"),
    )
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATA_FILE = DATA_DIR / "casino_data.json"

START_BALANCE = 1000

data_lock = threading.RLock()


# =========================================================
# DISCORD OAUTH
# =========================================================

DISCORD_CLIENT_ID = os.getenv(
    "DISCORD_CLIENT_ID"
)

DISCORD_CLIENT_SECRET = os.getenv(
    "DISCORD_CLIENT_SECRET"
)

DISCORD_REDIRECT_URI = (
    "https://dev-ehrp-vc-bot.onrender.com/"
    "auth/discord/callback"
)

DISCORD_API = "https://discord.com/api/v10"

DISCORD_AUTHORIZE_URL = (
    "https://discord.com/oauth2/authorize"
)

DISCORD_TOKEN_URL = (
    f"{DISCORD_API}/oauth2/token"
)

DISCORD_USER_URL = (
    f"{DISCORD_API}/users/@me"
)


# =========================================================
# SESSION GAME DATA
# =========================================================

blackjack_sessions = {}
highlow_sessions = {}
mines_sessions = {}
crash_sessions = {}


# =========================================================
# DATA HELPERS
# =========================================================

def load_data():
    with data_lock:

        if not DATA_FILE.exists():
            return {}

        try:
            with DATA_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

                if isinstance(data, dict):
                    return data

        except Exception as error:
            print(
                "Casino-Daten konnten "
                f"nicht geladen werden: {error}"
            )

        return {}


def save_data(data):
    with data_lock:

        temp_file = DATA_FILE.with_suffix(
            ".tmp"
        )

        with temp_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temp_file,
            DATA_FILE,
        )


def ensure_player(
    data,
    user_id,
):
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {}

    player = data[user_id]

    defaults = {
        "balance": START_BALANCE,
        "games": 0,
        "wins": 0,
        "losses": 0,
        "biggest_win": 0,
        "total_won": 0,
        "total_lost": 0,
        "daily_last": None,
        "history": [],
        "discord_username": None,
        "discord_avatar": None,
    }

    changed = False

    for key, value in defaults.items():

        if key not in player:

            player[key] = value
            changed = True

    return player, changed


def get_player(
    user_id,
):
    data = load_data()

    player, changed = ensure_player(
        data,
        user_id,
    )

    if changed:
        save_data(data)

    return player


def save_player_identity(
    user_id,
    username,
    avatar_url,
):
    data = load_data()

    player, _ = ensure_player(
        data,
        user_id,
    )

    player["discord_username"] = username
    player["discord_avatar"] = avatar_url

    save_data(data)


# =========================================================
# AUTH HELPERS
# =========================================================

def get_logged_in_user_id():

    user = session.get(
        "discord_user"
    )

    if not user:
        return None

    return str(
        user.get("id")
    )


def require_logged_in_user():

    user_id = get_logged_in_user_id()

    if not user_id:
        return None

    return user_id


def discord_avatar_url(
    user,
):
    avatar = user.get("avatar")
    user_id = user.get("id")

    if not avatar:
        return (
            "https://cdn.discordapp.com/"
            "embed/avatars/0.png"
        )

    extension = (
        "gif"
        if str(avatar).startswith("a_")
        else "png"
    )

    return (
        "https://cdn.discordapp.com/"
        f"avatars/{user_id}/{avatar}.{extension}"
        "?size=256"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    logged_in = bool(
        session.get(
            "discord_user"
        )
    )

    return render_template(
        "casino.html",
        logged_in=logged_in,
    )


# =========================================================
# ASSETS
# =========================================================

@app.route(
    "/assets/<path:filename>"
)
def assets(filename):

    return send_from_directory(
        ASSETS_DIR,
        filename,
    )


# =========================================================
# DISCORD LOGIN
# =========================================================

@app.route(
    "/auth/discord/login"
)
def discord_login():

    if (
        not DISCORD_CLIENT_ID
        or not DISCORD_CLIENT_SECRET
    ):
        return (
            "Discord OAuth ist "
            "nicht konfiguriert.",
            500,
        )

    state = secrets.token_urlsafe(32)

    session[
        "discord_oauth_state"
    ] = state

    params = {
        "client_id":
            DISCORD_CLIENT_ID,

        "redirect_uri":
            DISCORD_REDIRECT_URI,

        "response_type":
            "code",

        "scope":
            "identify",

        "state":
            state,

        "prompt":
            "none",
    }

    from urllib.parse import urlencode

    return redirect(
        DISCORD_AUTHORIZE_URL
        + "?"
        + urlencode(params)
    )


@app.route(
    "/auth/discord/callback"
)
def discord_callback():

    error = request.args.get(
        "error"
    )

    if error:
        return redirect(
            url_for("index")
        )

    code = request.args.get(
        "code"
    )

    state = request.args.get(
        "state"
    )

    expected_state = session.pop(
        "discord_oauth_state",
        None,
    )

    if (
        not code
        or not state
        or not expected_state
        or not secrets.compare_digest(
            state,
            expected_state,
        )
    ):
        return (
            "Ungültiger OAuth-Status.",
            400,
        )

    token_response = requests.post(
        DISCORD_TOKEN_URL,
        data={
            "client_id":
                DISCORD_CLIENT_ID,

            "client_secret":
                DISCORD_CLIENT_SECRET,

            "grant_type":
                "authorization_code",

            "code":
                code,

            "redirect_uri":
                DISCORD_REDIRECT_URI,
        },
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded"
        },
        timeout=15,
    )

    if not token_response.ok:
        print(
            "Discord Token Fehler:",
            token_response.text,
        )

        return (
            "Discord Login "
            "fehlgeschlagen.",
            400,
        )

    token_data = (
        token_response.json()
    )

    access_token = (
        token_data.get(
            "access_token"
        )
    )

    if not access_token:
        return (
            "Kein Discord "
            "Access Token erhalten.",
            400,
        )

    user_response = requests.get(
        DISCORD_USER_URL,
        headers={
            "Authorization":
                f"Bearer {access_token}"
        },
        timeout=15,
    )

    if not user_response.ok:
        return (
            "Discord Benutzer konnte "
            "nicht geladen werden.",
            400,
        )

    discord_user = (
        user_response.json()
    )

    user_id = str(
        discord_user["id"]
    )

    username = (
        discord_user.get(
            "global_name"
        )
        or discord_user.get(
            "username"
        )
        or "Discord User"
    )

    avatar_url = discord_avatar_url(
        discord_user
    )

    session["discord_user"] = {
        "id": user_id,
        "username": username,
        "avatar_url": avatar_url,
    }

    save_player_identity(
        user_id,
        username,
        avatar_url,
    )

    return redirect(
        url_for("index")
    )


@app.route(
    "/auth/discord/logout"
)
def discord_logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# AUTH STATUS
# =========================================================

@app.route(
    "/api/me"
)
def api_me():

    user = session.get(
        "discord_user"
    )

    if not user:
        return jsonify({
            "ok": False,
            "logged_in": False,
        })

    return jsonify({
        "ok": True,
        "logged_in": True,
        "user": user,
    })


# =========================================================
# PLAYER
# =========================================================

@app.route(
    "/api/player"
)
def api_player():

    user_id = require_logged_in_user()

    if not user_id:

        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    player = get_player(
        user_id
    )

    return jsonify({
        "ok": True,
        **player,
    })


# =========================================================
# BET
# =========================================================

def parse_bet(
    player,
    raw_bet,
):

    balance = int(
        player.get(
            "balance",
            0,
        )
    )

    if raw_bet == "all":
        bet = balance

    else:
        try:
            bet = int(
                raw_bet
            )
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


# =========================================================
# FINISH GAME
# =========================================================

def finish_game(
    user_id,
    bet,
    profit,
    game,
    result,
    detail=None,
):

    data = load_data()

    player, _ = ensure_player(
        data,
        user_id,
    )

    player["balance"] = int(
        player.get(
            "balance",
            0,
        )
    ) + int(profit)

    player["games"] = int(
        player.get(
            "games",
            0,
        )
    ) + 1

    if profit > 0:

        player["wins"] = int(
            player.get(
                "wins",
                0,
            )
        ) + 1

        player["total_won"] = int(
            player.get(
                "total_won",
                0,
            )
        ) + int(profit)

        player["biggest_win"] = max(
            int(
                player.get(
                    "biggest_win",
                    0,
                )
            ),
            int(profit),
        )

    elif profit < 0:

        player["losses"] = int(
            player.get(
                "losses",
                0,
            )
        ) + 1

        player["total_lost"] = int(
            player.get(
                "total_lost",
                0,
            )
        ) + abs(
            int(profit)
        )

    history = player.get(
        "history",
        []
    )

    if not isinstance(
        history,
        list,
    ):
        history = []

    history.insert(
        0,
        {
            "game": game,
            "bet": bet,
            "profit": profit,
            "result": result,
            "detail": detail or {},
        },
    )

    player["history"] = history[:50]

    save_data(data)

    return player


# =========================================================
# CARD HELPERS
# =========================================================

SUITS = [
    "♠",
    "♥",
    "♦",
    "♣",
]

RANKS = [
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


def make_deck():

    deck = [
        {
            "rank": rank,
            "suit": suit,
        }
        for suit in SUITS
        for rank in RANKS
    ]

    random.shuffle(
        deck
    )

    return deck


def card_value(card):

    rank = card["rank"]

    if rank in {
        "J",
        "Q",
        "K",
    }:
        return 10

    if rank == "A":
        return 11

    return int(rank)


def hand_value(hand):

    value = sum(
        card_value(card)
        for card in hand
    )

    aces = sum(
        1
        for card in hand
        if card["rank"] == "A"
    )

    while (
        value > 21
        and aces > 0
    ):
        value -= 10
        aces -= 1

    return value


# =========================================================
# BLACKJACK START
# =========================================================

@app.post(
    "/api/blackjack/start"
)
def blackjack_start():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Bitte zuerst mit "
                "Discord einloggen.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    player = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player,
            body.get("bet"),
        )

    except ValueError as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 400

    deck = make_deck()

    player_hand = [
        deck.pop(),
        deck.pop(),
    ]

    dealer_hand = [
        deck.pop(),
        deck.pop(),
    ]

    player_value = hand_value(
        player_hand
    )

    dealer_value = hand_value(
        dealer_hand
    )

    if player_value == 21:

        if dealer_value == 21:

            profit = 0
            result = "push"

        else:

            profit = int(
                bet * 1.5
            )

            result = "blackjack"

        final_player = finish_game(
            user_id,
            bet,
            profit,
            "blackjack",
            result,
        )

        return jsonify({
            "ok": True,
            "finished": True,
            "result": result,
            "profit": profit,
            "player_hand":
                player_hand,
            "dealer_hand":
                dealer_hand,
            "player_value":
                player_value,
            "dealer_value":
                dealer_value,
            "player":
                final_player,
        })

    blackjack_sessions[
        user_id
    ] = {
        "deck": deck,
        "player_hand":
            player_hand,
        "dealer_hand":
            dealer_hand,
        "bet": bet,
    }

    return jsonify({
        "ok": True,
        "finished": False,
        "player_hand":
            player_hand,
        "dealer_hand": [
            dealer_hand[0],
            {
                "rank": "?",
                "suit": "?",
            },
        ],
        "player_value":
            player_value,
        "dealer_value": "?",
    })


# =========================================================
# BLACKJACK HIT
# =========================================================

@app.post(
    "/api/blackjack/hit"
)
def blackjack_hit():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = blackjack_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    game[
        "player_hand"
    ].append(
        game["deck"].pop()
    )

    value = hand_value(
        game["player_hand"]
    )

    if value > 21:

        bet = game["bet"]

        profit = -bet

        player = finish_game(
            user_id,
            bet,
            profit,
            "blackjack",
            "bust",
        )

        blackjack_sessions.pop(
            user_id,
            None,
        )

        return jsonify({
            "ok": True,
            "finished": True,
            "result": "bust",
            "profit": profit,
            "player_hand":
                game["player_hand"],
            "dealer_hand":
                game["dealer_hand"],
            "player_value":
                value,
            "dealer_value":
                hand_value(
                    game[
                        "dealer_hand"
                    ]
                ),
            "player":
                player,
        })

    return jsonify({
        "ok": True,
        "finished": False,
        "player_hand":
            game["player_hand"],
        "dealer_hand": [
            game[
                "dealer_hand"
            ][0],
            {
                "rank": "?",
                "suit": "?",
            },
        ],
        "player_value":
            value,
        "dealer_value": "?",
    })


# =========================================================
# BLACKJACK STAND
# =========================================================

@app.post(
    "/api/blackjack/stand"
)
def blackjack_stand():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = blackjack_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    dealer_hand = game[
        "dealer_hand"
    ]

    while hand_value(
        dealer_hand
    ) < 17:
        dealer_hand.append(
            game[
                "deck"
            ].pop()
        )

    player_value = hand_value(
        game[
            "player_hand"
        ]
    )

    dealer_value = hand_value(
        dealer_hand
    )

    bet = game["bet"]

    if dealer_value > 21:

        profit = bet
        result = "dealer_bust"

    elif player_value > dealer_value:

        profit = bet
        result = "win"

    elif player_value < dealer_value:

        profit = -bet
        result = "lose"

    else:

        profit = 0
        result = "push"

    player = finish_game(
        user_id,
        bet,
        profit,
        "blackjack",
        result,
    )

    blackjack_sessions.pop(
        user_id,
        None,
    )

    return jsonify({
        "ok": True,
        "finished": True,
        "result": result,
        "profit": profit,
        "player_hand":
            game["player_hand"],
        "dealer_hand":
            dealer_hand,
        "player_value":
            player_value,
        "dealer_value":
            dealer_value,
        "player":
            player,
    })


# =========================================================
# HIGH / LOW START
# =========================================================

@app.post(
    "/api/highlow/start"
)
def highlow_start():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    player = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player,
            body.get("bet"),
        )

    except ValueError as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 400

    deck = make_deck()

    card = deck.pop()

    highlow_sessions[
        user_id
    ] = {
        "deck": deck,
        "card": card,
        "bet": bet,
    }

    return jsonify({
        "ok": True,
        "card": card,
        "value":
            card_value(card),
    })


# =========================================================
# HIGH / LOW GUESS
# =========================================================

@app.post(
    "/api/highlow/guess"
)
def highlow_guess():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = highlow_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    body = request.get_json(
        silent=True
    ) or {}

    guess = body.get(
        "guess"
    )

    if guess not in {
        "higher",
        "lower",
    }:
        return jsonify({
            "ok": False,
            "error":
                "Ungültige Auswahl.",
        }), 400

    old_card = game["card"]

    new_card = game[
        "deck"
    ].pop()

    old_value = card_value(
        old_card
    )

    new_value = card_value(
        new_card
    )

    bet = game["bet"]

    if new_value == old_value:

        profit = 0
        result = "draw"

    else:

        correct = (
            guess == "higher"
            and new_value > old_value
        ) or (
            guess == "lower"
            and new_value < old_value
        )

        if correct:
            profit = bet
            result = "win"

        else:
            profit = -bet
            result = "lose"

    player = finish_game(
        user_id,
        bet,
        profit,
        "highlow",
        result,
    )

    highlow_sessions.pop(
        user_id,
        None,
    )

    return jsonify({
        "ok": True,
        "old_card":
            old_card,
        "new_card":
            new_card,
        "profit":
            profit,
        "result":
            result,
        "player":
            player,
    })


# =========================================================
# BACCARAT
# =========================================================

def baccarat_value(
    hand
):
    total = 0

    for card in hand:

        rank = card["rank"]

        if rank in {
            "10",
            "J",
            "Q",
            "K",
        }:
            value = 0

        elif rank == "A":
            value = 1

        else:
            value = int(rank)

        total += value

    return total % 10


@app.post(
    "/api/baccarat/play"
)
def baccarat_play():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    choice = body.get(
        "choice"
    )

    if choice not in {
        "player",
        "banker",
        "tie",
    }:

        return jsonify({
            "ok": False,
            "error":
                "Ungültige Auswahl.",
        }), 400

    player_data = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player_data,
            body.get("bet"),
        )

    except ValueError as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 400

    deck = make_deck()

    player_hand = [
        deck.pop(),
        deck.pop(),
    ]

    banker_hand = [
        deck.pop(),
        deck.pop(),
    ]

    player_total = baccarat_value(
        player_hand
    )

    banker_total = baccarat_value(
        banker_hand
    )

    if player_total < 6:
        player_hand.append(
            deck.pop()
        )

        player_total = baccarat_value(
            player_hand
        )

    if banker_total < 6:
        banker_hand.append(
            deck.pop()
        )

        banker_total = baccarat_value(
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

        else:
            profit = bet

        result = "win"

    else:

        profit = -bet
        result = "lose"

    player = finish_game(
        user_id,
        bet,
        profit,
        "baccarat",
        result,
    )

    return jsonify({
        "ok": True,
        "winner": winner,
        "profit": profit,
        "player_hand":
            player_hand,
        "banker_hand":
            banker_hand,
        "player_total":
            player_total,
        "banker_total":
            banker_total,
        "player":
            player,
    })


# =========================================================
# MINES
# =========================================================

@app.post(
    "/api/mines/start"
)
def mines_start():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    player = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player,
            body.get("bet"),
        )

    except ValueError as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 400

    mine_count = 4

    mines = random.sample(
        range(16),
        mine_count,
    )

    mines_sessions[
        user_id
    ] = {
        "bet": bet,
        "mines": mines,
        "opened": [],
    }

    return jsonify({
        "ok": True,
        "mine_count":
            mine_count,
    })


@app.post(
    "/api/mines/open"
)
def mines_open():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = mines_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    body = request.get_json(
        silent=True
    ) or {}

    try:
        cell = int(
            body.get("cell")
        )

    except Exception:
        return jsonify({
            "ok": False,
            "error":
                "Ungültiges Feld.",
        }), 400

    if cell < 0 or cell > 15:

        return jsonify({
            "ok": False,
            "error":
                "Ungültiges Feld.",
        }), 400

    if cell in game["opened"]:

        return jsonify({
            "ok": False,
            "error":
                "Feld bereits geöffnet.",
        }), 400

    if cell in game["mines"]:

        bet = game["bet"]

        profit = -bet

        player = finish_game(
            user_id,
            bet,
            profit,
            "mines",
            "mine",
        )

        mines = game["mines"]

        mines_sessions.pop(
            user_id,
            None,
        )

        return jsonify({
            "ok": True,
            "hit_mine": True,
            "profit": profit,
            "mines": mines,
            "player": player,
        })

    game["opened"].append(
        cell
    )

    opened_count = len(
        game["opened"]
    )

    multiplier = round(
        1
        + opened_count * 0.24,
        2,
    )

    return jsonify({
        "ok": True,
        "hit_mine": False,
        "multiplier":
            multiplier,
    })


@app.post(
    "/api/mines/cashout"
)
def mines_cashout():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = mines_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    opened_count = len(
        game["opened"]
    )

    if opened_count == 0:

        return jsonify({
            "ok": False,
            "error":
                "Öffne zuerst "
                "mindestens ein Feld.",
        }), 400

    multiplier = round(
        1
        + opened_count * 0.24,
        2,
    )

    bet = game["bet"]

    profit = int(
        bet * (
            multiplier - 1
        )
    )

    player = finish_game(
        user_id,
        bet,
        profit,
        "mines",
        "cashout",
    )

    mines = game["mines"]

    mines_sessions.pop(
        user_id,
        None,
    )

    return jsonify({
        "ok": True,
        "profit": profit,
        "multiplier":
            multiplier,
        "mines": mines,
        "player": player,
    })


# =========================================================
# CRASH
# =========================================================

@app.post(
    "/api/crash/start"
)
def crash_start():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    player = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player,
            body.get("bet"),
        )

    except ValueError as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 400

    crash_point = round(
        random.uniform(
            1.05,
            8.0,
        ),
        2,
    )

    crash_sessions[
        user_id
    ] = {
        "bet": bet,
        "multiplier": 1.0,
        "crash_point":
            crash_point,
    }

    return jsonify({
        "ok": True,
    })


@app.post(
    "/api/crash/tick"
)
def crash_tick():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = crash_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    game["multiplier"] = round(
        game["multiplier"]
        + random.uniform(
            0.03,
            0.12,
        ),
        2,
    )

    if (
        game["multiplier"]
        >= game["crash_point"]
    ):

        bet = game["bet"]

        profit = -bet

        player = finish_game(
            user_id,
            bet,
            profit,
            "crash",
            "crashed",
        )

        multiplier = game[
            "multiplier"
        ]

        crash_sessions.pop(
            user_id,
            None,
        )

        return jsonify({
            "ok": True,
            "crashed": True,
            "multiplier":
                multiplier,
            "profit": profit,
            "player": player,
        })

    return jsonify({
        "ok": True,
        "crashed": False,
        "multiplier":
            game[
                "multiplier"
            ],
    })


@app.post(
    "/api/crash/cashout"
)
def crash_cashout():

    user_id = require_logged_in_user()

    if not user_id:
        return jsonify({
            "ok": False,
            "error":
                "Nicht eingeloggt.",
        }), 401

    game = crash_sessions.get(
        user_id
    )

    if not game:
        return jsonify({
            "ok": False,
            "error":
                "Keine aktive Runde.",
        }), 400

    multiplier = game[
        "multiplier"
    ]

    bet = game["bet"]

    profit = int(
        bet * (
            multiplier - 1
        )
    )

    player = finish_game(
        user_id,
        bet,
        profit,
        "crash",
        "cashout",
    )

    crash_sessions.pop(
        user_id,
        None,
    )

    return jsonify({
        "ok": True,
        "multiplier":
            multiplier,
        "profit":
            profit,
        "player":
            player,
    })


# =========================================================
# QUICK GAMES
# =========================================================

@app.post(
    "/api/play"
)
def play():

    user_id = require_logged_in_user()

    if not user_id:

        return jsonify({
            "ok": False,
            "error":
                "Bitte zuerst mit "
                "Discord einloggen.",
        }), 401

    body = request.get_json(
        silent=True
    ) or {}

    game = body.get(
        "game"
    )

    player_data = get_player(
        user_id
    )

    try:
        bet = parse_bet(
            player_data,
            body.get("bet"),
        )

    except ValueError as error:

        return jsonify({
            "ok": False,
            "error":
                str(error),
        }), 400


    # -----------------------------------------------------
    # SLOTS
    # -----------------------------------------------------

    if game == "slots":

        symbols = [
            "🍒",
            "🍋",
            "🔔",
            "👑",
            "💎",
            "7️⃣",
        ]

        reels = [
            random.choice(symbols)
            for _ in range(3)
        ]

        if (
            reels[0]
            == reels[1]
            == reels[2]
        ):

            profit = bet * 5
            result = "jackpot"

        elif len(
            set(reels)
        ) == 2:

            profit = bet
            result = "win"

        else:

            profit = -bet
            result = "lose"

        detail = {
            "reels": reels
        }


    # -----------------------------------------------------
    # DICE
    # -----------------------------------------------------

    elif game == "dice":

        you = random.randint(
            1,
            6,
        )

        casino = random.randint(
            1,
            6,
        )

        if you > casino:

            profit = bet
            result = "win"

        elif you < casino:

            profit = -bet
            result = "lose"

        else:

            profit = 0
            result = "draw"

        detail = {
            "you": you,
            "casino": casino,
        }


    # -----------------------------------------------------
    # COINFLIP
    # -----------------------------------------------------

    elif game == "coinflip":

        choice = body.get(
            "choice"
        )

        if choice not in {
            "Kopf",
            "Zahl",
        }:

            return jsonify({
                "ok": False,
                "error":
                    "Ungültige Auswahl.",
            }), 400

        coin_result = random.choice(
            [
                "Kopf",
                "Zahl",
            ]
        )

        if choice == coin_result:

            profit = bet
            result = "win"

        else:

            profit = -bet
            result = "lose"

        detail = {
            "result":
                coin_result
        }


    # -----------------------------------------------------
    # ROULETTE
    # -----------------------------------------------------

    elif game == "roulette":

        choice = body.get(
            "choice"
        )

        if choice not in {
            "red",
            "black",
            "green",
        }:

            return jsonify({
                "ok": False,
                "error":
                    "Ungültige Auswahl.",
            }), 400

        number = random.randint(
            0,
            36,
        )

        red_numbers = {
            1,
            3,
            5,
            7,
            9,
            12,
            14,
            16,
            18,
            19,
            21,
            23,
            25,
            27,
            30,
            32,
            34,
            36,
        }

        if number == 0:
            roulette_result = "green"

        elif number in red_numbers:
            roulette_result = "red"

        else:
            roulette_result = "black"

        if choice == roulette_result:

            if choice == "green":
                profit = bet * 14

            else:
                profit = bet

            result = "win"

        else:

            profit = -bet
            result = "lose"

        detail = {
            "number": number,
            "result":
                roulette_result,
        }


    else:

        return jsonify({
            "ok": False,
            "error":
                "Unbekanntes Spiel.",
        }), 400


    player = finish_game(
        user_id,
        bet,
        profit,
        game,
        result,
        detail,
    )


    return jsonify({
        "ok": True,
        "profit":
            profit,
        "result":
            result,
        "detail":
            detail,
        "player":
            player,
    })


# =========================================================
# LOCAL START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
