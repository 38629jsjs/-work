import requests, time, random, json, re, websocket, threading, os
from datetime import datetime
import pytz

# ==========================================
# SECTION 1: SETUP & CONFIGURATION (ENV VARS)
# ==========================================

# Pulling data from Koyeb Environment Variables
MAIN_ID = os.getenv("MAIN_ID")
MAIN_TOKEN = os.getenv("MAIN_TOKEN")

# We get the Alts as one long string and split it into a list
ALTS_RAW = os.getenv("ALTS_TOKENS", "")
ALTS = [t.strip() for t in ALTS_RAW.split(",") if t.strip()]

ECO_CHANNEL = os.getenv("ECO_CHANNEL")
GW_CHANNEL = os.getenv("GW_CHANNEL", ECO_CHANNEL)
KH_TZ = pytz.timezone('Asia/Phnom_Penh')

is_farming = True
rentals = {} # {user_id: expiration_timestamp}

# ==========================================
# SECTION 2: THE FULL ARMY GRINDER
# ==========================================
def farmer_loop():
    time.sleep(10)
    if not MAIN_TOKEN or not ALTS:
        print("❌ MISSING TOKENS IN KOYEB VARIABLES!")
        return

    FULL_SQUAD = [MAIN_TOKEN] + ALTS 
    
    while True:
        try:
            if is_farming:
                now = datetime.now(KH_TZ).strftime('%I:%M:%S %p')
                print(f"🚜 [{now}] --- GRIND STARTING ---")
                shuffled_squad = FULL_SQUAD[:]
                random.shuffle(shuffled_squad) 
                
                for t in shuffled_squad:
                    requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", 
                                  headers={"Authorization": t}, json={"content": "!work"})
                    time.sleep(random.uniform(3.0, 5.0)) 
                    requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", 
                                  headers={"Authorization": t}, json={"content": "!dep all"})
                    time.sleep(random.uniform(3.0, 5.0))

                print(f"💤 Cycle Finished. Sleeping 135s.")
                time.sleep(135) 
            else:
                time.sleep(30)
        except Exception:
            time.sleep(30)

# ==========================================
# SECTION 3: THE SNIPER
# ==========================================
def handle_snipes(content):
    nitro = re.search(r"discord(?:\.gift|app\.com/gifts)/([a-zA-Z0-9]+)", content)
    if nitro:
        code = nitro.group(1)
        threading.Thread(target=lambda: requests.post(f"https://discord.com/api/v9/entitlements/gift-codes/{code}/redeem", 
                        headers={"Authorization": MAIN_TOKEN}, json={"channel_id": GW_CHANNEL})).start()

# ==========================================
# SECTION 4: COMMAND MODULE (SINGLE ROB + RENT)
# ==========================================
def handle_all_commands(content, author_id):
    global is_farming, rentals
    cmd = content.lower().strip()
    now_ts = time.time()
    
    is_renter = author_id in rentals and now_ts < rentals[author_id]

    if author_id == MAIN_ID or is_renter:
        
        # 1. SINGLE ROB (.rob @user 3)
        if cmd.startswith(".rob "):
            try:
                parts = cmd.split(" ")
                victim = parts[1]
                idx = int(parts[2]) - 1
                if 0 <= idx < len(ALTS):
                    tok = ALTS[idx]
                    def execute():
                        requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tok}, json={"content": "!with all"})
                        time.sleep(2.0)
                        requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tok}, json={"content": "!pay ayngyl1 all"})
                        time.sleep(2.0)
                        requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tok}, json={"content": f"!rob {victim}"})
                        time.sleep(4.0)
                        requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tok}, json={"content": "!pay ayngyl1 all"})
                    threading.Thread(target=execute).start()
            except: pass

        # 2. RENT (.rent [ID] [Hours])
        elif author_id == MAIN_ID and cmd.startswith(".rent "):
            try:
                p = cmd.split(" ")
                rentals[p[1]] = now_ts + (int(p[2]) * 3600)
                requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": MAIN_TOKEN}, json={"content": f"✅ **RENTAL**: <@{p[1]}> active."})
            except: pass

        # 3. UTILITY
        elif cmd == ".flex":
            for i, t in enumerate(ALTS):
                threading.Thread(target=lambda tk=t, d=i*1.5: (time.sleep(d), requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tk}, json={"content": "!bal"}))).start()

        elif cmd == ".collect":
            for i, t in enumerate(ALTS):
                def coll(tk, d):
                    time.sleep(d)
                    requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tk}, json={"content": "!with all"})
                    time.sleep(2.0)
                    requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": tk}, json={"content": "!pay ayngyl1 all"})
                threading.Thread(target=coll, args=(t, i * 4.0)).start()

        elif cmd == ".stop" and author_id == MAIN_ID:
            is_farming = False
            requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": MAIN_TOKEN}, json={"content": "🛑 **Paused.**"})

        elif cmd == ".resume" and author_id == MAIN_ID:
            is_farming = True
            requests.post(f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages", headers={"Authorization": MAIN_TOKEN}, json={"content": "🚀 **Resumed.**"})

# ==========================================
# FINAL EXECUTION
# ==========================================
def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("t") == "MESSAGE_CREATE":
            m = data["d"]
            handle_snipes(m.get("content", ""))
            handle_all_commands(m.get("content", ""), m.get("author", {}).get("id"))
    except: pass

def run_bot():
    while True:
        try:
            ws = websocket.WebSocketApp("wss://gateway.discord.gg/?v=9&encoding=json", on_message=on_message)
            ws.on_open = lambda ws: ws.send(json.dumps({"op": 2, "d": {"token": MAIN_TOKEN, "properties": {"$os": "windows"}}}))
            ws.run_forever()
        except: time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=farmer_loop, daemon=True).start()
    run_bot()
