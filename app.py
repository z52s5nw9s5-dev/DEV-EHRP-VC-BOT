from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_from_directory,
)

from pathlib import Path

import json
import os
import random
import threading
import tempfile


# =========================================================
# EHRP/VC WEB CASINO
# =========================================================

app = Flask(__name__)


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

DATA_FILE = DATA_DIR / "casino_data.json"

START_BALANCE = 1000

lock = threading.RLock()


# =========================================================
# CASINO DATA
# =========================================================

def load():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            "{}",
            encoding="utf-8",
        )

    try:
        data = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
            or "{}"
        )

        if isinstance(data, dict):
            return data

        return {}

    except Exception as error:
        print(
            f"❌ Casino-Daten konnten "
            f"nicht geladen werden: {error}"
        )

        return {}


def save(data):
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temp_name = tempfile.mkstemp(
        dir=DATA_DIR,
        suffix=".tmp",
    )

    os.close(fd)

    temp_path = Path(temp_name)

    temp_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    os.replace(
        temp_path,
        DATA_FILE,
    )


# =========================================================
# PLAYER DATA
# =========================================================

def player(data, uid):
    uid = str(uid)

    p = data.setdefault(
        uid,
        {},
    )

    # WICHTIG:
    # setdefault erhält vorhandene Coins und Statistiken.
    # Bestehende Spieler werden NICHT zurückgesetzt.

    defaults = {
        "balance": START_BALANCE,
        "games": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "total_won": 0,
        "total_lost": 0,
        "biggest_win": 0,
    }

    for key, value in defaults.items():
        p.setdefault(
            key,
            value,
        )

    return p


# =========================================================
# WEBSITE
# =========================================================

@app.get("/")
def home():
    return render_template(
        "casino.html"
    )


# =========================================================
# ASSETS
# =========================================================

@app.get("/assets/<path:filename>")
def casino_assets(filename):
    return send_from_directory(
        ASSETS_DIR,
        filename,
    )


# =========================================================
# PLAYER API
# =========================================================

@app.get("/api/player/<uid>")
def get_player(uid):

    with lock:
        data = load()

        p = player(
            data,
            uid,
        )

        save(data)

        return jsonify(p)


# =========================================================
# PLAY API
# =========================================================

@app.post("/api/play")
def play():

    body = request.get_json(
        force=True
    )

    uid = str(
        body.get(
            "user_id",
            "demo",
        )
    )

    game = str(
        body.get(
            "game",
            "slots",
        )
    )

    bet = body.get(
        "bet",
        100,
    )


    with lock:

        data = load()

        p = player(
            data,
            uid,
        )


        # =================================================
        # BET
        # =================================================

        if bet == "all":
            bet = p["balance"]

        else:
            try:
                bet = int(bet)

            except (
                TypeError,
                ValueError,
            ):
                return jsonify(
                    {
                        "ok": False,
                        "error": "Ungültiger Einsatz",
                        "player": p,
                    }
                ), 400


        if bet <= 0:
            return jsonify(
                {
                    "ok": False,
                    "error": "Ungültiger Einsatz",
                    "player": p,
                }
            ), 400


        if p["balance"] < bet:
            return jsonify(
                {
                    "ok": False,
                    "error": "Nicht genügend Coins",
                    "player": p,
                }
            ), 400


        # =================================================
        # RESULT
        # =================================================

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
                "7️⃣",
            ]

            reels = [
                random.choice(symbols)
                for _ in range(3)
            ]

            detail = {
                "reels": reels
            }


            if len(set(reels)) == 1:

                multipliers = {
                    "7️⃣": 10,
                    "💎": 8,
                    "👑": 6,
                    "🔔": 4,
                    "🍒": 3,
                    "🍋": 3,
                }

                multiplier = (
                    multipliers[
                        reels[0]
                    ]
                )

                profit = (
                    bet
                    * (
                        multiplier
                        - 1
                    )
                )

                win = True


            elif len(set(reels)) == 2:

                profit = max(
                    1,
                    bet // 2,
                )

                win = True


            else:

                profit = -bet


        # =================================================
        # DICE
        # =================================================

        elif game == "dice":

            you = random.randint(
                1,
                6,
            )

            casino = random.randint(
                1,
                6,
            )

            detail = {
                "you": you,
                "casino": casino,
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
                "Kopf",
            )

            result = random.choice(
                [
                    "Kopf",
                    "Zahl",
                ]
            )

            detail = {
                "choice": choice,
                "result": result,
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
                "red",
            )

            number = random.randint(
                0,
                36,
            )

            reds = {
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

                color = "green"

            elif number in reds:

                color = "red"

            else:

                color = "black"


            detail = {
                "number": number,
                "color": color,
            }


            if choice == color:

                if choice == "green":

                    profit = (
                        bet
                        * 35
                    )

                else:

                    profit = bet

                win = True


            else:

                profit = -bet


        # =================================================
        # TEMPORARY GAME ENGINE
        #
        # Blackjack, Baccarat, High/Low, Mines und Crash
        # bekommen später eigene Engines.
        # =================================================

        else:

            roll = random.random()

            detail = {
                "roll": round(
                    roll,
                    3,
                )
            }


            if roll > 0.52:

                profit = bet
                win = True


            else:

                profit = -bet


        # =================================================
        # UPDATE PLAYER
        # =================================================

        p["balance"] += profit

        p["games"] += 1


        if draw:

            p["draws"] += 1


        elif win:

            p["wins"] += 1

            p["total_won"] += max(
                0,
                profit,
            )

            p["biggest_win"] = max(
                p["biggest_win"],
                profit,
            )


        else:

            p["losses"] += 1

            p["total_lost"] += abs(
                profit
            )


        # =================================================
        # SAVE
        # =================================================

        save(data)


        return jsonify(
            {
                "ok": True,
                "profit": profit,
                "detail": detail,
                "player": p,
            }
        )


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
        use_reloader=False,
    )
