/* =========================================================
   EHRP/VC CASINO ENGINE
========================================================= */

const USER_ID = window.USER_ID || "demo";

let selectedBet = 100;
let currentGame = null;
let isPlaying = false;


/* =========================================================
   GAMES
========================================================= */

const casinoGames = [
    {
        id: "slots",
        name: "SLOTS",
        icon: "🎰",
        description: "Drei Walzen. Ein Spin. Hol dir den Jackpot."
    },
    {
        id: "blackjack",
        name: "BLACKJACK",
        icon: "🂡",
        description: "Schlage den Dealer und komm so nah wie möglich an 21."
    },
    {
        id: "roulette",
        name: "ROULETTE",
        icon: "🎡",
        description: "Rot, Schwarz oder Grün. Setze und lass das Rad entscheiden."
    },
    {
        id: "coinflip",
        name: "COINFLIP",
        icon: "🪙",
        description: "Kopf oder Zahl. Einfach, schnell und 50/50."
    },
    {
        id: "dice",
        name: "DICE",
        icon: "🎲",
        description: "Dein Würfel gegen das Casino."
    },
    {
        id: "baccarat",
        name: "BACCARAT",
        icon: "🃏",
        description: "Player gegen Banker."
    },
    {
        id: "highlow",
        name: "HIGH / LOW",
        icon: "♦️",
        description: "Ist die nächste Karte höher oder niedriger?"
    },
    {
        id: "mines",
        name: "MINES",
        icon: "💣",
        description: "Finde Gewinne und vermeide die Minen."
    },
    {
        id: "crash",
        name: "CRASH",
        icon: "🚀",
        description: "Cashout bevor der Multiplikator crasht."
    }
];


/* =========================================================
   HELPERS
========================================================= */

function formatCoins(value) {
    return Number(value || 0).toLocaleString("de-DE");
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getGame(id) {
    return casinoGames.find(game => game.id === id);
}


/* =========================================================
   BETS
========================================================= */

function renderBets() {

    const container = document.getElementById("bets");

    if (!container) return;

    container.innerHTML = "";

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

    bets.forEach(bet => {

        const button = document.createElement("button");

        button.type = "button";

        button.textContent =
            bet === "all"
                ? "ALL IN"
                : formatCoins(bet);

        if (bet === selectedBet) {
            button.classList.add("active");
        }

        button.addEventListener("click", () => {

            if (isPlaying) return;

            selectedBet = bet;

            renderBets();

            updateGameBetText();
        });

        container.appendChild(button);
    });
}


/* =========================================================
   CASINO FLOOR
========================================================= */

function renderGames() {

    const grid = document.getElementById("gamesGrid");

    if (!grid) return;

    grid.innerHTML = "";

    casinoGames.forEach(game => {

        const card = document.createElement("article");

        card.className = "card";

        card.innerHTML = `
            <div class="icon">${game.icon}</div>
            <h3>${game.name}</h3>
            <p>${game.description}</p>
        `;

        card.addEventListener("click", () => {
            openGame(game.id);
        });

        grid.appendChild(card);
    });
}


/* =========================================================
   PLAYER
========================================================= */

async function loadPlayer() {

    try {

        const response = await fetch(
            `/api/player/${encodeURIComponent(USER_ID)}`
        );

        if (!response.ok) {
            throw new Error("Player konnte nicht geladen werden.");
        }

        const player = await response.json();

        updatePlayerUI(player);

    } catch (error) {

        console.error(error);

    }
}


function updatePlayerUI(player) {

    if (!player) return;

    const balance = document.getElementById("balance");
    const games = document.getElementById("games");
    const wins = document.getElementById("wins");
    const biggest = document.getElementById("biggest");
    const rate = document.getElementById("rate");

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

        const winrate =
            player.games > 0
                ? Math.round(
                    (player.wins / player.games) * 100
                )
                : 0;

        rate.textContent =
            `${winrate}%`;
    }
}


/* =========================================================
   GAME MODAL
========================================================= */

function openGame(gameId) {

    const game = getGame(gameId);

    if (!game) return;

    currentGame = gameId;

    const modal = document.getElementById("modal");
    const icon = document.getElementById("gameIcon");
    const title = document.getElementById("gameTitle");

    if (!modal) return;

    if (icon) {
        icon.textContent = game.icon;
    }

    if (title) {
        title.textContent = game.name;
    }

    modal.classList.remove("hidden");

    renderGameInterface();
}


function closeGame() {

    if (isPlaying) return;

    const modal = document.getElementById("modal");

    if (modal) {
        modal.classList.add("hidden");
    }

    currentGame = null;
}


function updateGameBetText() {

    if (!currentGame) return;

    const result = document.getElementById("result");

    if (!result) return;

    result.textContent =
        selectedBet === "all"
            ? "Einsatz: ALL IN"
            : `Einsatz: ${formatCoins(selectedBet)} Coins`;
}


/* =========================================================
   GAME INTERFACES
========================================================= */

function renderGameInterface() {

    const machine = document.getElementById("machine");
    const result = document.getElementById("result");
    const playButton = document.getElementById("playBtn");

    if (!machine || !result || !playButton) return;

    playButton.disabled = false;

    playButton.textContent = "JETZT SPIELEN";

    result.textContent =
        selectedBet === "all"
            ? "Einsatz: ALL IN"
            : `Einsatz: ${formatCoins(selectedBet)} Coins`;


    /* =====================================================
       SLOTS
    ====================================================== */

    if (currentGame === "slots") {

        machine.innerHTML = `
            <div class="slot-machine">
                <div class="slot-reel" id="reel1">7️⃣</div>
                <div class="slot-reel" id="reel2">💎</div>
                <div class="slot-reel" id="reel3">👑</div>
            </div>
        `;

        playButton.textContent = "🎰 SPIN";

        return;
    }


    /* =====================================================
       ROULETTE
    ====================================================== */

    if (currentGame === "roulette") {

        machine.innerHTML = `
            <div class="roulette-game">
                <div class="roulette-game-wheel">
                    🎡
                </div>

                <div class="roulette-choices">
                    <button
                        type="button"
                        class="roulette-choice roulette-red active"
                        data-choice="red"
                    >
                        ROT
                    </button>

                    <button
                        type="button"
                        class="roulette-choice roulette-black"
                        data-choice="black"
                    >
                        SCHWARZ
                    </button>

                    <button
                        type="button"
                        class="roulette-choice roulette-green"
                        data-choice="green"
                    >
                        0
                    </button>
                </div>
            </div>
        `;

        setupRouletteChoices();

        playButton.textContent = "🎡 DREHEN";

        return;
    }


    /* =====================================================
       COINFLIP
    ====================================================== */

    if (currentGame === "coinflip") {

        machine.innerHTML = `
            <div class="coinflip-game">

                <div
                    class="casino-coin"
                    id="casinoCoin"
                >
                    🪙
                </div>

                <div class="coin-choices">

                    <button
                        type="button"
                        class="coin-choice active"
                        data-choice="Kopf"
                    >
                        KOPF
                    </button>

                    <button
                        type="button"
                        class="coin-choice"
                        data-choice="Zahl"
                    >
                        ZAHL
                    </button>

                </div>

            </div>
        `;

        setupCoinChoices();

        playButton.textContent = "🪙 WERFEN";

        return;
    }


    /* =====================================================
       DICE
    ====================================================== */

    if (currentGame === "dice") {

        machine.innerHTML = `
            <div class="dice-game">

                <div class="dice-side">
                    <small>DU</small>
                    <div id="yourDice">⚄</div>
                </div>

                <div class="dice-vs">
                    VS
                </div>

                <div class="dice-side">
                    <small>CASINO</small>
                    <div id="casinoDice">⚂</div>
                </div>

            </div>
        `;

        playButton.textContent = "🎲 WÜRFELN";

        return;
    }


    /* =====================================================
       BLACKJACK
    ====================================================== */

    if (currentGame === "blackjack") {

        machine.innerHTML = `
            <div class="blackjack-preview">

                <div>
                    <small>DEALER</small>
                    <strong>🂠 🂠</strong>
                </div>

                <div class="blackjack-line"></div>

                <div>
                    <small>DU</small>
                    <strong>🂡 🂮</strong>
                </div>

            </div>
        `;

        result.textContent =
            "Blackjack-Tisch wird als Nächstes vollständig ausgebaut.";

        playButton.textContent =
            "🃏 RUNDE STARTEN";

        return;
    }


    /* =====================================================
       MINES
    ====================================================== */

    if (currentGame === "mines") {

        machine.innerHTML = `
            <div class="mines-preview">

                ${Array.from(
                    { length: 16 },
                    () => "<span>◆</span>"
                ).join("")}

            </div>
        `;

        playButton.textContent =
            "💣 MINES STARTEN";

        return;
    }


    /* =====================================================
       CRASH
    ====================================================== */

    if (currentGame === "crash") {

        machine.innerHTML = `
            <div class="crash-preview">

                <div id="crashMultiplier">
                    1.00×
                </div>

                <div>
                    🚀
                </div>

            </div>
        `;

        playButton.textContent =
            "🚀 START";

        return;
    }


    /* =====================================================
       OTHER
    ====================================================== */

    machine.innerHTML = `
        <div class="generic-game">
            ${getGame(currentGame)?.icon || "🎰"}
        </div>
    `;
}


/* =========================================================
   ROULETTE CHOICE
========================================================= */

let rouletteChoice = "red";

function setupRouletteChoices() {

    rouletteChoice = "red";

    document
        .querySelectorAll(".roulette-choice")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    if (isPlaying) return;

                    document
                        .querySelectorAll(".roulette-choice")
                        .forEach(item => {
                            item.classList.remove("active");
                        });

                    button.classList.add("active");

                    rouletteChoice =
                        button.dataset.choice;
                }
            );
        });
}


/* =========================================================
   COIN CHOICE
========================================================= */

let coinChoice = "Kopf";

function setupCoinChoices() {

    coinChoice = "Kopf";

    document
        .querySelectorAll(".coin-choice")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    if (isPlaying) return;

                    document
                        .querySelectorAll(".coin-choice")
                        .forEach(item => {
                            item.classList.remove("active");
                        });

                    button.classList.add("active");

                    coinChoice =
                        button.dataset.choice;
                }
            );
        });
}


/* =========================================================
   API PLAY
========================================================= */

async function requestPlay(extra = {}) {

    const response = await fetch(
        "/api/play",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                user_id: USER_ID,
                game: currentGame,
                bet: selectedBet,
                ...extra
            })
        }
    );

    const data = await response.json();

    if (!response.ok || !data.ok) {

        throw new Error(
            data.error ||
            "Spiel konnte nicht gestartet werden."
        );
    }

    return data;
}


/* =========================================================
   SLOT ANIMATION
========================================================= */

const slotSymbols = [
    "🍒",
    "🍋",
    "🔔",
    "👑",
    "💎",
    "7️⃣"
];


async function animateSlots(finalReels) {

    const reels = [
        document.getElementById("reel1"),
        document.getElementById("reel2"),
        document.getElementById("reel3")
    ];

    const timers = [];

    reels.forEach(reel => {

        if (!reel) return;

        reel.classList.add("spinning");

        const timer = setInterval(
            () => {

                reel.textContent =
                    slotSymbols[
                        Math.floor(
                            Math.random()
                            * slotSymbols.length
                        )
                    ];

            },
            70
        );

        timers.push(timer);
    });


    await sleep(850);

    clearInterval(timers[0]);

    reels[0].classList.remove("spinning");
    reels[0].textContent = finalReels[0];


    await sleep(300);

    clearInterval(timers[1]);

    reels[1].classList.remove("spinning");
    reels[1].textContent = finalReels[1];


    await sleep(350);

    clearInterval(timers[2]);

    reels[2].classList.remove("spinning");
    reels[2].textContent = finalReels[2];
}


/* =========================================================
   DICE ANIMATION
========================================================= */

const diceFaces = [
    "⚀",
    "⚁",
    "⚂",
    "⚃",
    "⚄",
    "⚅"
];


async function animateDice(you, casino) {

    const yourDice =
        document.getElementById("yourDice");

    const casinoDice =
        document.getElementById("casinoDice");


    for (let i = 0; i < 12; i++) {

        if (yourDice) {
            yourDice.textContent =
                diceFaces[
                    Math.floor(
                        Math.random() * 6
                    )
                ];
        }

        if (casinoDice) {
            casinoDice.textContent =
                diceFaces[
                    Math.floor(
                        Math.random() * 6
                    )
                ];
        }

        await sleep(70);
    }


    if (yourDice) {
        yourDice.textContent =
            diceFaces[you - 1];
    }

    if (casinoDice) {
        casinoDice.textContent =
            diceFaces[casino - 1];
    }
}


/* =========================================================
   COIN ANIMATION
========================================================= */

async function animateCoin(result) {

    const coin =
        document.getElementById("casinoCoin");

    if (!coin) return;

    coin.classList.add("flipping");

    await sleep(1100);

    coin.classList.remove("flipping");

    coin.textContent =
        result === "Kopf"
            ? "👑"
            : "🪙";
}


/* =========================================================
   ROULETTE ANIMATION
========================================================= */

async function animateRoulette(number) {

    const wheel =
        document.querySelector(
            ".roulette-game-wheel"
        );

    if (!wheel) return;

    wheel.classList.add("roulette-spinning");

    await sleep(1500);

    wheel.classList.remove(
        "roulette-spinning"
    );

    wheel.textContent =
        number;
}


/* =========================================================
   RESULT
========================================================= */

function showResult(data) {

    const result =
        document.getElementById("result");

    if (!result) return;


    if (data.profit > 0) {

        result.innerHTML =
            `🔥 GEWONNEN: <strong>+${formatCoins(
                data.profit
            )} Coins</strong>`;

        result.className =
            "result-win";

    } else if (data.profit < 0) {

        result.innerHTML =
            `Verloren: <strong>${formatCoins(
                data.profit
            )} Coins</strong>`;

        result.className =
            "result-loss";

    } else {

        result.textContent =
            "Unentschieden.";

        result.className =
            "result-draw";
    }
}


/* =========================================================
   PLAY CURRENT GAME
========================================================= */

async function playCurrentGame() {

    if (
        isPlaying ||
        !currentGame
    ) {
        return;
    }


    isPlaying = true;


    const playButton =
        document.getElementById("playBtn");

    const result =
        document.getElementById("result");


    if (playButton) {

        playButton.disabled = true;

        playButton.textContent =
            "LÄUFT...";
    }


    if (result) {

        result.className = "";

        result.textContent =
            "Casino entscheidet...";
    }


    try {

        let extra = {};


        if (currentGame === "roulette") {

            extra.choice =
                rouletteChoice;
        }


        if (currentGame === "coinflip") {

            extra.choice =
                coinChoice;
        }


        const data =
            await requestPlay(extra);


        /* =============================================
           SLOT
        ============================================== */

        if (
            currentGame === "slots" &&
            data.detail?.reels
        ) {

            await animateSlots(
                data.detail.reels
            );
        }


        /* =============================================
           DICE
        ============================================== */

        else if (
            currentGame === "dice"
        ) {

            await animateDice(
                data.detail.you,
                data.detail.casino
            );
        }


        /* =============================================
           COINFLIP
        ============================================== */

        else if (
            currentGame === "coinflip"
        ) {

            await animateCoin(
                data.detail.result
            );
        }


        /* =============================================
           ROULETTE
        ============================================== */

        else if (
            currentGame === "roulette"
        ) {

            await animateRoulette(
                data.detail.number
            );
        }


        /* =============================================
           GENERIC
        ============================================== */

        else {

            await sleep(900);
        }


        updatePlayerUI(
            data.player
        );


        showResult(data);


    } catch (error) {

        if (result) {

            result.className =
                "result-loss";

            result.textContent =
                error.message;
        }

    } finally {

        isPlaying = false;


        if (playButton) {

            playButton.disabled =
                false;


            if (
                currentGame ===
                "slots"
            ) {

                playButton.textContent =
                    "🎰 NOCHMAL SPINNEN";

            } else if (
                currentGame ===
                "roulette"
            ) {

                playButton.textContent =
                    "🎡 NOCHMAL DREHEN";

            } else if (
                currentGame ===
                "coinflip"
            ) {

                playButton.textContent =
                    "🪙 NOCHMAL";

            } else if (
                currentGame ===
                "dice"
            ) {

                playButton.textContent =
                    "🎲 NOCHMAL WÜRFELN";

            } else {

                playButton.textContent =
                    "NOCHMAL SPIELEN";
            }
        }
    }
}


/* =========================================================
   EVENTS
========================================================= */

const playButton =
    document.getElementById("playBtn");

if (playButton) {

    playButton.addEventListener(
        "click",
        playCurrentGame
    );
}


const modal =
    document.getElementById("modal");

if (modal) {

    modal.addEventListener(
        "click",
        event => {

            if (
                event.target === modal &&
                !isPlaying
            ) {

                closeGame();
            }
        }
    );
}


/* =========================================================
   START
========================================================= */

renderBets();
renderGames();
loadPlayer();
