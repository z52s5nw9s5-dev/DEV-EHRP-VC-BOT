const casinoGames = [
    ["slots", "🎰", "SLOTS", "Goldene Walzen & Multiplikatoren"],
    ["blackjack", "🃏", "BLACKJACK", "Schlag den Dealer"],
    ["roulette", "🎡", "ROULETTE", "Rot, Schwarz oder Zero"],
    ["coinflip", "🪙", "COINFLIP", "Kopf oder Zahl"],
    ["dice", "🎲", "DICE", "Dein Wurf gegen das Casino"],
    ["baccarat", "👑", "BACCARAT", "Player gegen Banker"],
    ["highlow", "⬆️", "HIGH / LOW", "Ist die nächste Karte höher?"],
    ["mines", "💣", "MINES", "Risiko Feld für Feld"],
    ["crash", "🚀", "CRASH", "Cashout vor dem Absturz"]
];

let selectedBet = 100;
let currentGame = null;

const USER_ID =
    window.USER_ID ||
    new URLSearchParams(window.location.search).get("uid") ||
    "demo";


function formatCoins(value) {
    return Number(value || 0).toLocaleString("de-DE");
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


/* =========================================================
   BETS
========================================================= */

function renderBets() {

    const container = document.getElementById("bets");

    if (!container) {
        return;
    }

    const bets = [
        50,
        100,
        250,
        500,
        1000,
        2500,
        5000,
        10000,
        "all"
    ];

    container.innerHTML = "";

    for (const value of bets) {

        const button = document.createElement("button");

        const isActive =
            String(selectedBet) === String(value);

        if (isActive) {
            button.classList.add("active");
        }

        if (value === "all") {
            button.textContent = "🔥 ALLES REIN";
        } else {
            button.textContent = formatCoins(value);
        }

        button.addEventListener(
            "click",
            () => {

                selectedBet = value;

                renderBets();

                if (currentGame) {
                    updateGameBetText();
                }

            }
        );

        container.appendChild(button);
    }
}


/* =========================================================
   GAME CARDS
========================================================= */

function renderGames() {

    const grid =
        document.getElementById("gamesGrid");

    if (!grid) {
        return;
    }

    grid.innerHTML = "";

    for (const game of casinoGames) {

        const [
            id,
            icon,
            title,
            description
        ] = game;

        const card =
            document.createElement("div");

        card.className = "card";

        card.innerHTML = `
            <div class="icon">
                ${icon}
            </div>

            <h3>
                ${title}
            </h3>

            <p>
                ${description}
            </p>
        `;

        card.addEventListener(
            "click",
            () => openGame(id)
        );

        grid.appendChild(card);
    }
}


/* =========================================================
   PLAYER
========================================================= */

async function loadPlayer() {

    try {

        const response =
            await fetch(
                `/api/player/${encodeURIComponent(USER_ID)}`,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const player =
            await response.json();

        updatePlayerUI(player);

    } catch (error) {

        console.error(
            "Spielerdaten konnten nicht geladen werden:",
            error
        );

    }
}


function updatePlayerUI(player) {

    if (!player) {
        return;
    }

    const balance =
        document.getElementById("balance");

    const games =
        document.getElementById("games");

    const wins =
        document.getElementById("wins");

    const biggest =
        document.getElementById("biggest");

    const rate =
        document.getElementById("rate");


    if (balance) {
        balance.textContent =
            formatCoins(player.balance);
    }

    if (games) {
        games.textContent =
            formatCoins(player.games);
    }

    if (wins) {
        wins.textContent =
            formatCoins(player.wins);
    }

    if (biggest) {
        biggest.textContent =
            formatCoins(player.biggest_win);
    }

    if (rate) {

        const total =
            Number(player.games || 0);

        const won =
            Number(player.wins || 0);

        const winrate =
            total > 0
                ? Math.round(
                    (won / total) * 100
                )
                : 0;

        rate.textContent =
            `${winrate}%`;
    }
}


/* =========================================================
   GAME WINDOW
========================================================= */

function openGame(gameId) {

    currentGame = gameId;

    const game =
        casinoGames.find(
            item => item[0] === gameId
        );

    if (!game) {
        return;
    }

    const modal =
        document.getElementById("modal");

    const icon =
        document.getElementById("gameIcon");

    const title =
        document.getElementById("gameTitle");

    const machine =
        document.getElementById("machine");


    icon.textContent =
        game[1];

    title.textContent =
        game[2];


    if (gameId === "slots") {

        machine.textContent =
            "❔　❔　❔";

    } else if (gameId === "roulette") {

        machine.textContent =
            "🎡  ◆  🎡";

    } else if (gameId === "blackjack") {

        machine.textContent =
            "🂠　🂠";

    } else if (gameId === "dice") {

        machine.textContent =
            "🎲　VS　🎲";

    } else if (gameId === "coinflip") {

        machine.textContent =
            "🪙";

    } else if (gameId === "mines") {

        machine.textContent =
            "◆　◆　◆";

    } else if (gameId === "crash") {

        machine.textContent =
            "🚀 1.00×";

    } else {

        machine.textContent =
            "◆　READY　◆";
    }


    updateGameBetText();

    modal.classList.remove("hidden");
}


function closeGame() {

    const modal =
        document.getElementById("modal");

    modal.classList.add("hidden");

    currentGame = null;
}


function updateGameBetText() {

    const result =
        document.getElementById("result");

    if (!result) {
        return;
    }

    if (selectedBet === "all") {

        result.textContent =
            "Einsatz: 🔥 ALLES REIN";

    } else {

        result.textContent =
            `Einsatz: ${formatCoins(selectedBet)} EHRP Coins`;
    }
}


/* =========================================================
   SLOT ANIMATION
========================================================= */

async function animateSlots() {

    const machine =
        document.getElementById("machine");

    const symbols = [
        "🍒",
        "🔔",
        "👑",
        "💎",
        "7️⃣"
    ];

    for (
        let frame = 0;
        frame < 18;
        frame++
    ) {

        const reels = [];

        for (
            let reel = 0;
            reel < 3;
            reel++
        ) {

            reels.push(
                symbols[
                    Math.floor(
                        Math.random() *
                        symbols.length
                    )
                ]
            );
        }

        machine.textContent =
            reels.join("　");

        await sleep(
            45 + frame * 7
        );
    }
}


/* =========================================================
   ROULETTE ANIMATION
========================================================= */

async function animateRoulette() {

    const machine =
        document.getElementById("machine");

    for (
        let i = 0;
        i < 20;
        i++
    ) {

        const number =
            Math.floor(
                Math.random() * 37
            );

        machine.textContent =
            `🎡 ${number}`;

        await sleep(
            40 + i * 8
        );
    }
}


/* =========================================================
   DICE ANIMATION
========================================================= */

async function animateDice() {

    const machine =
        document.getElementById("machine");

    const dice = [
        "⚀",
        "⚁",
        "⚂",
        "⚃",
        "⚄",
        "⚅"
    ];

    for (
        let i = 0;
        i < 12;
        i++
    ) {

        const left =
            dice[
                Math.floor(
                    Math.random() * 6
                )
            ];

        const right =
            dice[
                Math.floor(
                    Math.random() * 6
                )
            ];

        machine.textContent =
            `${left}　VS　${right}`;

        await sleep(
            70 + i * 5
        );
    }
}


/* =========================================================
   COIN ANIMATION
========================================================= */

async function animateCoinflip() {

    const machine =
        document.getElementById("machine");

    for (
        let i = 0;
        i < 12;
        i++
    ) {

        machine.textContent =
            i % 2 === 0
                ? "🪙 KOPF"
                : "🪙 ZAHL";

        await sleep(
            80
        );
    }
}


/* =========================================================
   GENERIC ANIMATION
========================================================= */

async function animateGeneric() {

    const machine =
        document.getElementById("machine");

    const frames = [
        "◇",
        "◆",
        "◇",
        "◆"
    ];

    for (
        let i = 0;
        i < 10;
        i++
    ) {

        machine.textContent =
            `${frames[i % frames.length]}  PLAYING  ${frames[i % frames.length]}`;

        await sleep(90);
    }
}


/* =========================================================
   PLAY
========================================================= */

async function playCurrentGame() {

    if (!currentGame) {
        return;
    }

    const button =
        document.getElementById("playBtn");

    const result =
        document.getElementById("result");

    const machine =
        document.getElementById("machine");


    button.disabled = true;

    result.textContent =
        "Spiel läuft …";


    try {

        if (currentGame === "slots") {

            await animateSlots();

        } else if (
            currentGame === "roulette"
        ) {

            await animateRoulette();

        } else if (
            currentGame === "dice"
        ) {

            await animateDice();

        } else if (
            currentGame === "coinflip"
        ) {

            await animateCoinflip();

        } else {

            await animateGeneric();
        }


        const payload = {
            user_id: USER_ID,
            game: currentGame,
            bet: selectedBet
        };


        /*
         * Vorläufige Standardauswahl.
         * Später bekommt jedes Spiel seine
         * vollständige eigene Oberfläche.
         */

        if (
            currentGame === "coinflip"
        ) {

            payload.choice =
                "Kopf";
        }


        if (
            currentGame === "roulette"
        ) {

            payload.choice =
                "red";
        }


        const response =
            await fetch(
                "/api/play",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            result.textContent =
                data.error ||
                "Das Spiel konnte nicht gestartet werden.";

            return;
        }


        /* =============================================
           FINAL VISUAL RESULT
        ============================================== */

        if (
            currentGame === "slots" &&
            data.detail &&
            Array.isArray(
                data.detail.reels
            )
        ) {

            machine.textContent =
                data.detail.reels.join(
                    "　"
                );

        }


        else if (
            currentGame === "roulette" &&
            data.detail
        ) {

            const number =
                data.detail.number;

            const color =
                String(
                    data.detail.color ||
                    ""
                ).toUpperCase();

            machine.textContent =
                `🎡 ${number}  ${color}`;
        }


        else if (
            currentGame === "dice" &&
            data.detail
        ) {

            machine.textContent =
                `🎲 ${data.detail.you}  :  ${data.detail.casino} 🎲`;
        }


        else if (
            currentGame === "coinflip" &&
            data.detail
        ) {

            machine.textContent =
                `🪙 ${data.detail.result}`;
        }


        else {

            if (
                Number(data.profit) >= 0
            ) {

                machine.textContent =
                    "✨  WIN  ✨";

            } else {

                machine.textContent =
                    "◆  HOUSE WINS  ◆";
            }
        }


        /* =============================================
           RESULT TEXT
        ============================================== */

        const profit =
            Number(
                data.profit || 0
            );


        if (profit > 0) {

            result.textContent =
                `+${formatCoins(profit)} EHRP Coins`;

        } else if (profit < 0) {

            result.textContent =
                `${formatCoins(profit)} EHRP Coins`;

        } else {

            result.textContent =
                "Unentschieden";
        }


        /* =============================================
           UPDATE PLAYER
        ============================================== */

        updatePlayerUI(
            data.player
        );


    } catch (error) {

        console.error(
            "Casino Fehler:",
            error
        );

        result.textContent =
            "Verbindungsfehler – bitte erneut versuchen.";

    } finally {

        button.disabled = false;
    }
}


/* =========================================================
   EVENTS
========================================================= */

document
    .getElementById("playBtn")
    ?.addEventListener(
        "click",
        playCurrentGame
    );


document
    .getElementById("modal")
    ?.addEventListener(
        "click",
        event => {

            if (
                event.target.id ===
                "modal"
            ) {

                closeGame();
            }

        }
    );


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key ===
            "Escape"
        ) {

            closeGame();
        }

    }
);


/* =========================================================
   START
========================================================= */

renderBets();

renderGames();

loadPlayer();
