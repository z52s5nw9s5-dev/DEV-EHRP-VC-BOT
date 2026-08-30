
const games=[
["slots","🎰","SLOTS","Goldene Walzen & Multiplikatoren"],["blackjack","🃏","BLACKJACK","Schlag den Dealer"],
["roulette","🎡","ROULETTE","Setz auf Rot, Schwarz oder Zero"],["coinflip","🪙","COINFLIP","Kopf oder Zahl"],
["dice","🎲","DICE","Dein Wurf gegen das Casino"],["baccarat","👑","BACCARAT","Player gegen Banker"],
["highlow","⬆️","HIGH / LOW","Ist die nächste Karte höher?"],["mines","💣","MINES","Risiko Feld für Feld"],
["crash","🚀","CRASH","Cashout vor dem Absturz"]];
let bet=100,current=null;
const fmt=n=>Number(n).toLocaleString("de-DE");
function renderBets(){let vals=[50,100,250,500,1000,2500,5000,10000,"all"];bets.innerHTML=vals.map(v=>`<button class="${v===bet?'active':''}" onclick="bet='${v}';renderBets()">${v==="all"?"🔥 ALLES REIN":fmt(v)}</button>`).join("")}
function renderGames(){gamesGrid.innerHTML=games.map(g=>`<div class="card" onclick="openGame('${g[0]}')"><div class="icon">${g[1]}</div><h3>${g[2]}</h3><p>${g[3]}</p></div>`).join("")}
async function loadPlayer(){let p=await fetch(`/api/player/${USER_ID}`).then(r=>r.json());balance.textContent=fmt(p.balance);let gamesEl=p.games||0;document.getElementById("games").textContent=fmt(gamesEl);wins.textContent=fmt(p.wins||0);biggest.textContent=fmt(p.biggest_win||0);rate.textContent=gamesEl?Math.round((p.wins||0)/gamesEl*100)+"%":"0%"}
function openGame(id){current=id;let g=games.find(x=>x[0]===id);gameIcon.textContent=g[1];gameTitle.textContent=g[2];machine.textContent=id==="slots"?"❔　❔　❔":"◆　READY　◆";result.textContent="Einsatz: "+(bet==="all"?"ALLES REIN":fmt(bet)+" Coins");modal.classList.remove("hidden")}
function closeGame(){modal.classList.add("hidden")}
playBtn.onclick=async()=>{playBtn.disabled=true;machine.classList.add("spin");if(current==="slots"){let seq=["🍒","💎","7️⃣","👑","🔔"];for(let i=0;i<10;i++){machine.textContent=[0,1,2].map(()=>seq[Math.floor(Math.random()*seq.length)]).join("　");await new Promise(r=>setTimeout(r,70+i*10))}}
let body={user_id:USER_ID,game:current,bet:bet};if(current==="coinflip")body.choice="Kopf";if(current==="roulette")body.choice="red";
let res=await fetch("/api/play",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});let d=await res.json();
if(d.ok){if(d.detail.reels)machine.textContent=d.detail.reels.join("　");else if(d.detail.number!==undefined)machine.textContent="🎡 "+d.detail.number+" "+d.detail.color.toUpperCase();else if(d.detail.you)machine.textContent=`🎲 ${d.detail.you} : ${d.detail.casino} 🎲`;else machine.textContent=d.profit>=0?"✨ WIN ✨":"◆ HOUSE WINS ◆";result.textContent=(d.profit>=0?"+":"")+fmt(d.profit)+" EHRP Coins";balance.textContent=fmt(d.player.balance);document.getElementById("games").textContent=fmt(d.player.games);wins.textContent=fmt(d.player.wins);biggest.textContent=fmt(d.player.biggest_win);rate.textContent=d.player.games?Math.round(d.player.wins/d.player.games*100)+"%":"0%"}else result.textContent=d.error||"Fehler";playBtn.disabled=false};
renderBets();renderGames();loadPlayer();
