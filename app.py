
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json, os, random, threading, tempfile

app = Flask(__name__)
DATA_DIR = Path(os.getenv("CASINO_DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "casino_data.json"
START_BALANCE = 1000
lock = threading.RLock()

def load():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
    try:
        data=json.loads(DATA_FILE.read_text(encoding="utf-8") or "{}")
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, name=tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    os.close(fd)
    Path(name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    os.replace(name, DATA_FILE)

def player(data, uid):
    p=data.setdefault(str(uid),{})
    defaults={"balance":START_BALANCE,"games":0,"wins":0,"losses":0,"draws":0,
              "total_won":0,"total_lost":0,"biggest_win":0}
    for k,v in defaults.items(): p.setdefault(k,v)
    return p

@app.get("/")
def home():
    return render_template("casino.html")

@app.get("/api/player/<uid>")
def get_player(uid):
    with lock:
        data=load(); p=player(data,uid); save(data)
        return jsonify(p)

@app.post("/api/play")
def play():
    body=request.get_json(force=True)
    uid=str(body.get("user_id","demo"))
    game=str(body.get("game","slots"))
    bet=body.get("bet",100)
    with lock:
        data=load(); p=player(data,uid)
        bet=p["balance"] if bet=="all" else int(bet)
        if bet<=0 or p["balance"]<bet:
            return jsonify({"ok":False,"error":"Nicht genügend Coins","player":p}),400

        win=False; draw=False; profit=0; detail={}
        if game=="slots":
            symbols=["🍒","🍋","🔔","👑","💎","7️⃣"]
            reels=[random.choice(symbols) for _ in range(3)]
            detail={"reels":reels}
            if len(set(reels))==1:
                mult={"7️⃣":10,"💎":8,"👑":6,"🔔":4,"🍒":3,"🍋":3}[reels[0]]
                profit=bet*(mult-1); win=True
            elif len(set(reels))==2:
                profit=bet//2; win=True
            else: profit=-bet
        elif game=="dice":
            a,b=random.randint(1,6),random.randint(1,6); detail={"you":a,"casino":b}
            if a>b: profit=bet; win=True
            elif a==b: draw=True
            else: profit=-bet
        elif game=="coinflip":
            choice=body.get("choice","Kopf")
            result=random.choice(["Kopf","Zahl"]); detail={"choice":choice,"result":result}
            if choice==result: profit=bet; win=True
            else: profit=-bet
        elif game=="roulette":
            choice=body.get("choice","red"); n=random.randint(0,36)
            reds={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
            color="green" if n==0 else ("red" if n in reds else "black")
            detail={"number":n,"color":color}
            good=(choice==color)
            if good:
                profit=bet*(35 if choice=="green" else 1); win=True
            else: profit=-bet
        else:
            # Prototype engine for the remaining visual game rooms.
            roll=random.random()
            detail={"roll":round(roll,3)}
            if roll>0.52: profit=bet; win=True
            else: profit=-bet

        p["balance"]+=profit; p["games"]+=1
        if draw: p["draws"]+=1
        elif win:
            p["wins"]+=1; p["total_won"]+=max(0,profit); p["biggest_win"]=max(p["biggest_win"],profit)
        else:
            p["losses"]+=1; p["total_lost"]+=abs(profit)
        save(data)
        return jsonify({"ok":True,"profit":profit,"detail":detail,"player":p})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")))
