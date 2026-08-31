/* =========================================================
   EHRP/VC CASINO — COMPLETE ENGINE
========================================================= */

const USER_ID = window.USER_ID || "demo";

let selectedBet = 100;
let currentGame = null;
let isPlaying = false;

let rouletteChoice = "red";
let coinChoice = "Kopf";
let baccaratChoice = "player";

let blackjackActive = false;
let highlowActive = false;
let minesActive = false;
let crashActive = false;

let crashTimer = null;


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
        description: "Rot, Schwarz oder Grün."
    },
    {
        id: "coinflip",
        name: "COINFLIP",
        icon: "🪙",
        description: "Kopf oder Zahl."
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
        description: "Öffne Felder und vermeide die Minen."
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

async function postJSON(url, body = {}) {

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Serverantwort konnte nicht gelesen werden.");
    }

    if (!response.ok || !data.ok) {
        throw new Error(
            data.error || "Casino-Fehler."
        );
    }

    return data;
}

function setResult(text, type = "") {

    const result = document.getElementById("result");

    if (!result) return;

    result.className = type;
    result.textContent = text;
}

function setPlayButton(text, disabled = false) {

    const button = document.getElementById("playBtn");

    if (!button) return;

    button.textContent = text;
    button.disabled = disabled;
    button.style.display = "";
}

function anyGameActive() {
    return (
        isPlaying ||
        blackjackActive ||
        highlowActive ||
        minesActive ||
        crashActive
    );
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

            if (anyGameActive()) return;

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

        card.addEventListener(
            "click",
            () => openGame(game.id)
        );

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
        balance.textContent = formatCoins(player.balance);
    }

    if (games) {
        games.textContent = formatCoins(player.games);
    }

    if (wins) {
        wins.textContent = formatCoins(player.wins);
    }

    if (biggest) {
        biggest.textContent = formatCoins(player.biggest_win);
    }

    if (rate) {

        const percentage =
            player.games > 0
                ? Math.round(
                    (player.wins / player.games) * 100
                )
                : 0;

        rate.textContent = `${percentage}%`;
    }
}


/* =========================================================
   MODAL
========================================================= */

function openGame(gameId) {

    if (anyGameActive()) return;

    const game = getGame(gameId);

    if (!game) return;

    currentGame = gameId;

    const modal = document.getElementById("modal");

    document.getElementById("gameIcon").textContent = game.icon;
    document.getElementById("gameTitle").textContent = game.name;

    modal.classList.remove("hidden");

    renderGameInterface();
}

function closeGame() {

    if (anyGameActive()) return;

    document
        .getElementById("modal")
        .classList.add("hidden");

    currentGame = null;
}

function updateGameBetText() {

    if (!currentGame) return;

    setResult(
        selectedBet === "all"
            ? "Einsatz: ALL IN"
            : `Einsatz: ${formatCoins(selectedBet)} Coins`
    );
}


/* =========================================================
   CARD HTML
========================================================= */

function cardHTML(card, hidden = false) {

    if (
        hidden ||
        !card ||
        card.rank === "?"
    ) {

        return `
            <div class="bj-card bj-card-back">
                <div class="bj-card-pattern">♛</div>
            </div>
        `;
    }

    const red =
        card.suit === "♥" ||
        card.suit === "♦";

    return `
        <div class="bj-card ${red ? "bj-red" : ""}">
            <div class="bj-rank">${card.rank}</div>
            <div class="bj-suit">${card.suit}</div>
            <div class="bj-rank bj-bottom">${card.rank}</div>
        </div>
    `;
}


/* =========================================================
   GAME INTERFACES
========================================================= */

function renderGameInterface() {

    const machine = document.getElementById("machine");

    setResult("");
    updateGameBetText();

    /* SLOTS */

    if (currentGame === "slots") {

        machine.innerHTML = `
            <div class="slot-machine">
                <div class="slot-reel" id="reel1">7️⃣</div>
                <div class="slot-reel" id="reel2">💎</div>
                <div class="slot-reel" id="reel3">👑</div>
            </div>
        `;

        setPlayButton("🎰 SPIN");
        return;
    }


    /* BLACKJACK */

    if (currentGame === "blackjack") {

        machine.innerHTML = `
            <div class="blackjack-lobby">
                <div class="blackjack-lobby-logo">♠</div>
                <strong>EHRP/VC BLACKJACK</strong>
                <small>DEALER STANDS ON 17</small>
            </div>
        `;

        setPlayButton("🃏 RUNDE STARTEN");
        return;
    }


    /* ROULETTE */

    if (currentGame === "roulette") {

        rouletteChoice = "red";

        machine.innerHTML = `
            <div class="roulette-game">

                <div class="roulette-game-wheel">
                    🎡
                </div>

                <div class="roulette-choices">

                    <button
                        class="roulette-choice roulette-red active"
                        data-choice="red"
                    >
                        ROT
                    </button>

                    <button
                        class="roulette-choice roulette-black"
                        data-choice="black"
                    >
                        SCHWARZ
                    </button>

                    <button
                        class="roulette-choice roulette-green"
                        data-choice="green"
                    >
                        0
                    </button>

                </div>

            </div>
        `;

        setupChoiceButtons(
            ".roulette-choice",
            value => rouletteChoice = value
        );

        setPlayButton("🎡 DREHEN");
        return;
    }


    /* COINFLIP */

    if (currentGame === "coinflip") {

        coinChoice = "Kopf";

        machine.innerHTML = `
            <div class="coinflip-game">

                <div class="casino-coin" id="casinoCoin">
                    🪙
                </div>

                <div class="coin-choices">

                    <button
                        class="coin-choice active"
                        data-choice="Kopf"
                    >
                        KOPF
                    </button>

                    <button
                        class="coin-choice"
                        data-choice="Zahl"
                    >
                        ZAHL
                    </button>

                </div>

            </div>
        `;

        setupChoiceButtons(
            ".coin-choice",
            value => coinChoice = value
        );

        setPlayButton("🪙 WERFEN");
        return;
    }


    /* DICE */

    if (currentGame === "dice") {

        machine.innerHTML = `
            <div class="dice-game">

                <div class="dice-side">
                    <small>DU</small>
                    <div id="yourDice">⚄</div>
                </div>

                <div class="dice-vs">VS</div>

                <div class="dice-side">
                    <small>CASINO</small>
                    <div id="casinoDice">⚂</div>
                </div>

            </div>
        `;

        setPlayButton("🎲 WÜRFELN");
        return;
    }


    /* BACCARAT */

    if (currentGame === "baccarat") {

        baccaratChoice = "player";

        machine.innerHTML = `
            <div class="blackjack-lobby">

                <div class="blackjack-lobby-logo">
                    🃏
                </div>

                <strong>BACCARAT</strong>

                <small>
                    WÄHLE DEINE SEITE
                </small>

                <div class="roulette-choices">

                    <button
                        class="roulette-choice active"
                        data-choice="player"
                    >
                        PLAYER
                    </button>

                    <button
                        class="roulette-choice"
                        data-choice="banker"
                    >
                        BANKER
                    </button>

                    <button
                        class="roulette-choice"
                        data-choice="tie"
                    >
                        TIE
                    </button>

                </div>

            </div>
        `;

        setupChoiceButtons(
            ".roulette-choice",
            value => baccaratChoice = value
        );

        setPlayButton("🃏 KARTEN GEBEN");
        return;
    }


    /* HIGH LOW */

    if (currentGame === "highlow") {

        machine.innerHTML = `
            <div class="blackjack-lobby">

                <div class="blackjack-lobby-logo">
                    ♦
                </div>

                <strong>HIGH / LOW</strong>

                <small>
                    STARTE DIE RUNDE
                </small>

            </div>
        `;

        setPlayButton("♦️ RUNDE STARTEN");
        return;
    }


    /* MINES */

    if (currentGame === "mines") {

        renderMinesBoard();

        setPlayButton("💣 MINES STARTEN");
        return;
    }


    /* CRASH */

    if (currentGame === "crash") {

        machine.innerHTML = `
            <div class="crash-preview">

                <div id="crashMultiplier">
                    1.00×
                </div>

                <div id="crashRocket">
                    🚀
                </div>

            </div>
        `;

        setPlayButton("🚀 START");
    }
}


/* =========================================================
   CHOICE BUTTONS
========================================================= */

function setupChoiceButtons(selector, callback) {

    document
        .querySelectorAll(selector)
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    if (isPlaying) return;

                    document
                        .querySelectorAll(selector)
                        .forEach(item => {
                            item.classList.remove("active");
                        });

                    button.classList.add("active");

                    callback(
                        button.dataset.choice
                    );
                }
            );
        });
}


/* =========================================================
   BLACKJACK TABLE
========================================================= */

function renderBlackjackTable(data) {

    const machine = document.getElementById("machine");

    machine.innerHTML = `
        <div class="blackjack-table">

            <div class="bj-area">

                <div class="bj-label">
                    DEALER
                    <span>${data.dealer_value ?? "?"}</span>
                </div>

                <div class="bj-hand">
                    ${data.dealer_hand
                        .map(card => cardHTML(card))
                        .join("")}
                </div>

            </div>

            <div class="bj-table-logo">
                ♛
                <small>EHRP/VC</small>
            </div>

            <div class="bj-area">

                <div class="bj-label">
                    DEINE HAND
                    <span>${data.player_value}</span>
                </div>

                <div class="bj-hand">
                    ${data.player_hand
                        .map(card => cardHTML(card))
                        .join("")}
                </div>

            </div>

            ${
                data.finished
                    ? ""
                    : `
                        <div class="bj-actions">

                            <button
                                class="bj-hit"
                                onclick="blackjackHit()"
                            >
                                + HIT
                            </button>

                            <button
                                class="bj-stand"
                                onclick="blackjackStand()"
                            >
                                STAND
                            </button>

                        </div>
                    `
            }

        </div>
    `;
}


/* =========================================================
   BLACKJACK START
========================================================= */

async function blackjackStart() {

    if (anyGameActive()) return;

    isPlaying = true;

    setPlayButton(
        "KARTEN WERDEN GEGEBEN...",
        true
    );

    setResult("Dealer mischt die Karten...");

    try {

        const data = await postJSON(
            "/api/blackjack/start",
            {
                user_id: USER_ID,
                bet: selectedBet
            }
        );

        renderBlackjackTable(data);

        if (data.player) {
            updatePlayerUI(data.player);
        }

        if (data.finished) {

            blackjackActive = false;

            showBlackjackResult(data);

            setPlayButton(
                "🃏 NEUE RUNDE"
            );

        } else {

            blackjackActive = true;

            setResult(
                `Deine Hand: ${data.player_value} — HIT oder STAND?`
            );

            document.getElementById(
                "playBtn"
            ).style.display = "none";
        }

    } catch (error) {

        blackjackActive = false;

        setResult(
            error.message,
            "result-loss"
        );

        setPlayButton(
            "🃏 RUNDE STARTEN"
        );

    } finally {

        isPlaying = false;
    }
}

async function blackjackHit() {

    if (
        !blackjackActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    try {

        const data = await postJSON(
            "/api/blackjack/hit",
            {
                user_id: USER_ID
            }
        );

        renderBlackjackTable(data);

        if (data.finished) {

            blackjackActive = false;

            showBlackjackResult(data);

            if (data.player) {
                updatePlayerUI(data.player);
            }

            setPlayButton(
                "🃏 NEUE RUNDE"
            );

        } else {

            setResult(
                `Deine Hand: ${data.player_value} — HIT oder STAND?`
            );
        }

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}

async function blackjackStand() {

    if (
        !blackjackActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    setResult("Dealer zieht...");

    try {

        const data = await postJSON(
            "/api/blackjack/stand",
            {
                user_id: USER_ID
            }
        );

        renderBlackjackTable(data);

        blackjackActive = false;

        showBlackjackResult(data);

        updatePlayerUI(data.player);

        setPlayButton(
            "🃏 NEUE RUNDE"
        );

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}

function showBlackjackResult(data) {

    const messages = {
        blackjack:
            `🃏 BLACKJACK! +${formatCoins(data.profit)} Coins`,
        dealer_blackjack:
            `Dealer hat Blackjack. ${formatCoins(data.profit)} Coins`,
        bust:
            `💥 BUST! ${formatCoins(data.profit)} Coins`,
        dealer_bust:
            `🔥 Dealer Bust! +${formatCoins(data.profit)} Coins`,
        win:
            `🔥 GEWONNEN! +${formatCoins(data.profit)} Coins`,
        lose:
            `Dealer gewinnt. ${formatCoins(data.profit)} Coins`,
        push:
            "🤝 PUSH — Unentschieden."
    };

    showProfitResult(
        data,
        messages[data.result] || "Runde beendet."
    );
}


/* =========================================================
   HIGH / LOW
========================================================= */

async function highlowStart() {

    if (anyGameActive()) return;

    isPlaying = true;

    setPlayButton(
        "KARTE WIRD GEZOGEN...",
        true
    );

    try {

        const data = await postJSON(
            "/api/highlow/start",
            {
                user_id: USER_ID,
                bet: selectedBet
            }
        );

        highlowActive = true;

        document.getElementById(
            "machine"
        ).innerHTML = `
            <div class="blackjack-table">

                <div class="bj-label">
                    AKTUELLE KARTE
                </div>

                <div class="bj-hand">
                    ${cardHTML(data.card)}
                </div>

                <div class="bj-actions">

                    <button
                        class="bj-hit"
                        onclick="highlowGuess('higher')"
                    >
                        ↑ HÖHER
                    </button>

                    <button
                        class="bj-stand"
                        onclick="highlowGuess('lower')"
                    >
                        ↓ TIEFER
                    </button>

                </div>

            </div>
        `;

        setResult(
            `Kartenwert ${data.value} — höher oder tiefer?`
        );

        document.getElementById(
            "playBtn"
        ).style.display = "none";

    } catch (error) {

        highlowActive = false;

        setResult(
            error.message,
            "result-loss"
        );

        setPlayButton(
            "♦️ RUNDE STARTEN"
        );

    } finally {

        isPlaying = false;
    }
}

async function highlowGuess(guess) {

    if (
        !highlowActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    try {

        const data = await postJSON(
            "/api/highlow/guess",
            {
                user_id: USER_ID,
                guess
            }
        );

        highlowActive = false;

        document.getElementById(
            "machine"
        ).innerHTML = `
            <div class="blackjack-table">

                <div class="bj-label">
                    VORHER
                </div>

                <div class="bj-hand">
                    ${cardHTML(data.old_card)}
                </div>

                <div class="bj-label">
                    NÄCHSTE KARTE
                </div>

                <div class="bj-hand">
                    ${cardHTML(data.new_card)}
                </div>

            </div>
        `;

        updatePlayerUI(data.player);

        showProfitResult(data);

        setPlayButton(
            "♦️ NEUE RUNDE"
        );

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}


/* =========================================================
   BACCARAT
========================================================= */

async function baccaratPlay() {

    if (anyGameActive()) return;

    isPlaying = true;

    setPlayButton(
        "KARTEN WERDEN GEGEBEN...",
        true
    );

    try {

        const data = await postJSON(
            "/api/baccarat/play",
            {
                user_id: USER_ID,
                bet: selectedBet,
                choice: baccaratChoice
            }
        );

        document.getElementById(
            "machine"
        ).innerHTML = `
            <div class="blackjack-table">

                <div class="bj-area">

                    <div class="bj-label">
                        PLAYER
                        <span>${data.player_total}</span>
                    </div>

                    <div class="bj-hand">
                        ${data.player_hand
                            .map(card => cardHTML(card))
                            .join("")}
                    </div>

                </div>

                <div class="bj-table-logo">
                    VS
                </div>

                <div class="bj-area">

                    <div class="bj-label">
                        BANKER
                        <span>${data.banker_total}</span>
                    </div>

                    <div class="bj-hand">
                        ${data.banker_hand
                            .map(card => cardHTML(card))
                            .join("")}
                    </div>

                </div>

            </div>
        `;

        updatePlayerUI(data.player);

        const winnerNames = {
            player: "PLAYER",
            banker: "BANKER",
            tie: "TIE"
        };

        showProfitResult(
            data,
            `${winnerNames[data.winner]} gewinnt — ${
                data.profit > 0
                    ? "+"
                    : ""
            }${formatCoins(data.profit)} Coins`
        );

        setPlayButton(
            "🃏 NOCHMAL"
        );

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

        setPlayButton(
            "🃏 KARTEN GEBEN"
        );

    } finally {

        isPlaying = false;
    }
}


/* =========================================================
   MINES
========================================================= */

function renderMinesBoard() {

    document.getElementById(
        "machine"
    ).innerHTML = `
        <div class="mines-preview" id="minesBoard">

            ${Array.from(
                { length: 16 },
                (_, index) => `
                    <span
                        data-cell="${index}"
                        onclick="minesOpen(${index})"
                    >
                        ◆
                    </span>
                `
            ).join("")}

        </div>
    `;
}

async function minesStart() {

    if (anyGameActive()) return;

    isPlaying = true;

    try {

        const data = await postJSON(
            "/api/mines/start",
            {
                user_id: USER_ID,
                bet: selectedBet
            }
        );

        minesActive = true;

        renderMinesBoard();

        setResult(
            `${data.mine_count} Minen versteckt — wähle ein Feld.`
        );

        setPlayButton(
            "💰 CASHOUT"
        );

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}

async function minesOpen(cell) {

    if (
        !minesActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    try {

        const data = await postJSON(
            "/api/mines/open",
            {
                user_id: USER_ID,
                cell
            }
        );

        const field = document.querySelector(
            `[data-cell="${cell}"]`
        );

        if (data.hit_mine) {

            minesActive = false;

            revealMines(data.mines);

            if (field) {
                field.textContent = "💣";
            }

            updatePlayerUI(data.player);

            showProfitResult(
                data,
                `💥 BOOM! ${formatCoins(data.profit)} Coins`
            );

            setPlayButton(
                "💣 NEUE RUNDE"
            );

        } else {

            if (field) {

                field.textContent = "💎";
                field.style.pointerEvents = "none";
            }

            setResult(
                `💎 Sicher! Multiplikator: ${Number(
                    data.multiplier
                ).toFixed(2)}×`
            );
        }

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}

function revealMines(mines = []) {

    mines.forEach(cell => {

        const field = document.querySelector(
            `[data-cell="${cell}"]`
        );

        if (field) {
            field.textContent = "💣";
        }
    });
}

async function minesCashout() {

    if (
        !minesActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    try {

        const data = await postJSON(
            "/api/mines/cashout",
            {
                user_id: USER_ID
            }
        );

        minesActive = false;

        revealMines(data.mines);

        updatePlayerUI(data.player);

        showProfitResult(
            data,
            `💰 CASHOUT ${Number(
                data.multiplier
            ).toFixed(2)}× — +${formatCoins(
                data.profit
            )} Coins`
        );

        setPlayButton(
            "💣 NEUE RUNDE"
        );

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;
    }
}


/* =========================================================
   CRASH
========================================================= */

async function crashStart() {

    if (anyGameActive()) return;

    isPlaying = true;

    try {

        await postJSON(
            "/api/crash/start",
            {
                user_id: USER_ID,
                bet: selectedBet
            }
        );

        crashActive = true;

        setPlayButton(
            "💰 CASHOUT"
        );

        setResult(
            "🚀 Der Multiplikator steigt..."
        );

        isPlaying = false;

        crashLoop();

    } catch (error) {

        crashActive = false;
        isPlaying = false;

        setResult(
            error.message,
            "result-loss"
        );
    }
}

async function crashLoop() {

    if (!crashActive) return;

    try {

        const data = await postJSON(
            "/api/crash/tick",
            {
                user_id: USER_ID
            }
        );

        const multiplier =
            document.getElementById(
                "crashMultiplier"
            );

        if (multiplier) {

            multiplier.textContent =
                `${Number(
                    data.multiplier
                ).toFixed(2)}×`;
        }

        if (data.crashed) {

            crashActive = false;

            if (data.player) {
                updatePlayerUI(data.player);
            }

            setResult(
                `💥 CRASH bei ${Number(
                    data.multiplier
                ).toFixed(2)}× — ${formatCoins(
                    data.profit
                )} Coins`,
                "result-loss"
            );

            setPlayButton(
                "🚀 NEUE RUNDE"
            );

            return;
        }

        crashTimer = setTimeout(
            crashLoop,
            180
        );

    } catch (error) {

        crashActive = false;

        setResult(
            error.message,
            "result-loss"
        );

        setPlayButton(
            "🚀 NEUE RUNDE"
        );
    }
}

async function crashCashout() {

    if (
        !crashActive ||
        isPlaying
    ) {
        return;
    }

    isPlaying = true;

    if (crashTimer) {

        clearTimeout(crashTimer);
        crashTimer = null;
    }

    try {

        const data = await postJSON(
            "/api/crash/cashout",
            {
                user_id: USER_ID
            }
        );

        crashActive = false;

        updatePlayerUI(data.player);

        setResult(
            `💰 CASHOUT bei ${Number(
                data.multiplier
            ).toFixed(2)}× — +${formatCoins(
                data.profit
            )} Coins`,
            "result-win"
        );

        setPlayButton(
            "🚀 NEUE RUNDE"
        );

    } catch (error) {

        crashActive = false;

        setResult(
            error.message,
            "result-loss"
        );

        setPlayButton(
            "🚀 NEUE RUNDE"
        );

    } finally {

        isPlaying = false;
    }
}


/* =========================================================
   QUICK GAMES
========================================================= */

const slotSymbols = [
    "🍒",
    "🍋",
    "🔔",
    "👑",
    "💎",
    "7️⃣"
];

const diceFaces = [
    "⚀",
    "⚁",
    "⚂",
    "⚃",
    "⚄",
    "⚅"
];

async function animateSlots(finalReels) {

    const reels = [
        document.getElementById("reel1"),
        document.getElementById("reel2"),
        document.getElementById("reel3")
    ];

    for (let spin = 0; spin < 12; spin++) {

        reels.forEach(reel => {

            if (!reel) return;

            reel.textContent =
                slotSymbols[
                    Math.floor(
                        Math.random() *
                        slotSymbols.length
                    )
                ];
        });

        await sleep(65);
    }

    reels.forEach((reel, index) => {

        if (reel) {
            reel.textContent = finalReels[index];
        }
    });
}

async function animateDice(you, casino) {

    const yourDice =
        document.getElementById("yourDice");

    const casinoDice =
        document.getElementById("casinoDice");

    for (let i = 0; i < 12; i++) {

        if (yourDice) {

            yourDice.textContent =
                diceFaces[
                    Math.floor(Math.random() * 6)
                ];
        }

        if (casinoDice) {

            casinoDice.textContent =
                diceFaces[
                    Math.floor(Math.random() * 6)
                ];
        }

        await sleep(60);
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

async function animateCoin(finalResult) {

    const coin =
        document.getElementById("casinoCoin");

    if (!coin) return;

    coin.classList.add("flipping");

    await sleep(900);

    coin.classList.remove("flipping");

    coin.textContent =
        finalResult === "Kopf"
            ? "👑"
            : "🪙";
}

async function animateRoulette(number) {

    const wheel =
        document.querySelector(
            ".roulette-game-wheel"
        );

    if (!wheel) return;

    wheel.classList.add(
        "roulette-spinning"
    );

    await sleep(1200);

    wheel.classList.remove(
        "roulette-spinning"
    );

    wheel.textContent = String(number);
}

async function quickGamePlay() {

    isPlaying = true;

    setPlayButton(
        "LÄUFT...",
        true
    );

    setResult(
        "Casino entscheidet..."
    );

    try {

        const extra = {};

        if (currentGame === "roulette") {
            extra.choice = rouletteChoice;
        }

        if (currentGame === "coinflip") {
            extra.choice = coinChoice;
        }

        const data = await postJSON(
            "/api/play",
            {
                user_id: USER_ID,
                game: currentGame,
                bet: selectedBet,
                ...extra
            }
        );

        if (
            currentGame === "slots" &&
            data.detail?.reels
        ) {

            await animateSlots(
                data.detail.reels
            );
        }

        if (currentGame === "dice") {

            await animateDice(
                data.detail.you,
                data.detail.casino
            );
        }

        if (currentGame === "coinflip") {

            await animateCoin(
                data.detail.result
            );
        }

        if (currentGame === "roulette") {

            await animateRoulette(
                data.detail.number
            );
        }

        updatePlayerUI(data.player);

        showProfitResult(data);

    } catch (error) {

        setResult(
            error.message,
            "result-loss"
        );

    } finally {

        isPlaying = false;

        const names = {
            slots: "🎰 NOCHMAL SPINNEN",
            roulette: "🎡 NOCHMAL DREHEN",
            coinflip: "🪙 NOCHMAL",
            dice: "🎲 NOCHMAL WÜRFELN"
        };

        setPlayButton(
            names[currentGame] ||
            "NOCHMAL SPIELEN"
        );
    }
}


/* =========================================================
   RESULT
========================================================= */

function showProfitResult(
    data,
    customMessage = null
) {

    if (customMessage) {

        setResult(
            customMessage,
            data.profit > 0
                ? "result-win"
                : data.profit < 0
                    ? "result-loss"
                    : "result-draw"
        );

        return;
    }

    if (data.profit > 0) {

        setResult(
            `🔥 GEWONNEN: +${formatCoins(
                data.profit
            )} Coins`,
            "result-win"
        );

    } else if (data.profit < 0) {

        setResult(
            `Verloren: ${formatCoins(
                data.profit
            )} Coins`,
            "result-loss"
        );

    } else {

        setResult(
            "🤝 Unentschieden.",
            "result-draw"
        );
    }
}


/* =========================================================
   MAIN PLAY BUTTON
========================================================= */

async function playCurrentGame() {

    if (!currentGame || isPlaying) return;

    if (currentGame === "blackjack") {

        await blackjackStart();
        return;
    }

    if (currentGame === "highlow") {

        await highlowStart();
        return;
    }

    if (currentGame === "baccarat") {

        await baccaratPlay();
        return;
    }

    if (currentGame === "mines") {

        if (minesActive) {
            await minesCashout();
        } else {
            await minesStart();
        }

        return;
    }

    if (currentGame === "crash") {

        if (crashActive) {
            await crashCashout();
        } else {
            await crashStart();
        }

        return;
    }

    await quickGamePlay();
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
                !anyGameActive()
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
