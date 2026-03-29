import requests, time, random, json, re, websocket, threading, os
from datetime import datetime
import pytz

# ==========================================
# SECTION 1: SETUP (ENV VARS)
# ==========================================
MAIN_ID = os.getenv("MAIN_ID")
MAIN_TOKEN = os.getenv("MAIN_TOKEN")
ALTS_RAW = os.getenv("ALTS_TOKENS", "")
ALTS = [t.strip() for t in ALTS_RAW.split(",") if t.strip()]
ECO_CHANNEL = os.getenv("ECO_CHANNEL")
GW_CHANNEL = os.getenv("GW_CHANNEL", ECO_CHANNEL)
KH_TZ = pytz.timezone('Asia/Phnom_Penh')

is_farming = True
rentals = {}

# Helper to send messages without lagging the main loop
def fast_post(token, content):
    url = f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages"
    # Small jitter (0.1s to 0.9s) so Discord doesn't see 6 identical timestamps
    time.sleep(random.uniform(0.1, 0.9))
    requests.post(url, headers={"Authorization": token}, json={"content": content})

# ==========================================
# SECTION 2: TURBO GRINDER (PARALLEL)
# ==========================================
def worker_task(token):
    """The actual grind logic for a single account"""
    fast_post(token, "!work")
    time.sleep(random.uniform(1.5, 2.5)) # Fast wait
    fast_post(token, "!dep all")

def farmer_loop():
    time.sleep(5)
    FULL_SQUAD = [MAIN_TOKEN] + ALTS 
    
    while True:
        try:
            if is_farming:
                now = datetime.now(KH_TZ).strftime('%I:%M:%S %p')
                print(f"🚀 [{now}] --- TURBO GRIND STARTING ---")
                
                threads = []
                for t in FULL_SQUAD:
                    # Fire off all accounts at once using threads
                    thread = threading.Thread(target=worker_task, args=(t,))
                    thread.start()
                    threads.append(thread)
                
                # Wait for all accounts to finish their work/dep cycle
                for thread in threads:
                    thread.join()

                print(f"💤 All accounts finished. Sleeping 135s.")
                time.sleep(135) 
            else:
                time.sleep(10)
        except Exception:
            time.sleep(10)

# ==========================================
# SECTION 4: ELITE COMMAND MODULE (FAST ROB)
# ==========================================

# Helper to send messages at maximum safe speed
def fast_post(token, content):
    url = f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages"
    # 0.1s to 0.4s jitter to stay under Discord's anti-spam radar
    time.sleep(random.uniform(0.1, 0.4))
    try:
        requests.post(url, headers={"Authorization": token}, json={"content": content})
    except:
        pass

def handle_all_commands(content, author_id):
    global is_farming, rentals
    cmd = content.lower().strip()
    now_ts = time.time()
    
    # Check if the sender is YOU or someone who RENTED the bot
    is_renter = author_id in rentals and now_ts < rentals[author_id]

    if author_id == MAIN_ID or is_renter:
        
        # 1. TURBO SINGLE ROB (.rob @user 1-5)
        if cmd.startswith(".rob "):
            try:
                parts = cmd.split(" ")
                victim = parts[1]
                idx = int(parts[2]) - 1
                
                if 0 <= idx < len(ALTS):
                    tok = ALTS[idx]
                    
                    def execute_fast_rob():
                        # Phase A: Empty Alt Wallet to your Main
                        fast_post(tok, "!with all")
                        time.sleep(1.1)
                        fast_post(tok, "!pay ayngyl1 all")
                        
                        # Phase B: The Attack
                        time.sleep(1.1)
                        fast_post(tok, f"!rob {victim}")
                        
                        # Phase C: Secure the Loot (2.5s for Bot Processing)
                        time.sleep(2.5) 
                        fast_post(tok, "!pay ayngyl1 all")
                        print(f"✅ Alt {idx + 1} finished Robbery on {victim}")

                    threading.Thread(target=execute_fast_rob).start()
            except: pass

        # 2. SIMULTANEOUS COLLECT (Waterfall of Cash)
        elif cmd == ".collect":
            def fast_collect(t):
                fast_post(t, "!with all")
                time.sleep(1.2)
                fast_post(t, "!pay ayngyl1 all")

            for t in ALTS:
                threading.Thread(target=fast_collect, args=(t,)).start()

        # 3. INSTANT FLEX (Check all balances at once)
        elif cmd == ".flex":
            for t in ALTS:
                threading.Thread(target=fast_post, args=(t, "!bal")).start()

        # 4. RENTAL SETUP (.rent [User_ID] [Hours])
        elif author_id == MAIN_ID and cmd.startswith(".rent "):
            try:
                p = cmd.split(" ")
                target_uid = p[1]
                duration = int(p[2])
                rentals[target_uid] = now_ts + (duration * 3600)
                fast_post(MAIN_TOKEN, f"✅ **RENTAL ACTIVE**: <@{target_uid}> for {duration}h.")
            except: pass

        # 5. FARM CONTROL
        elif cmd == ".stop" and author_id == MAIN_ID:
            is_farming = False
            fast_post(MAIN_TOKEN, "🛑 **Grinding Paused.**")

        elif cmd == ".resume" and author_id == MAIN_ID:
            is_farming = True
            fast_post(MAIN_TOKEN, "🚀 **Grinding Resumed.**")
# ==========================================
# SECTION 5: SYSTEM CORE
# ==========================================
def handle_snipes(content):
    nitro = re.search(r"discord(?:\.gift|app\.com/gifts)/([a-zA-Z0-9]+)", content)
    if nitro:
        code = nitro.group(1)
        threading.Thread(target=lambda: requests.post(f"https://discord.com/api/v9/entitlements/gift-codes/{code}/redeem", 
                        headers={"Authorization": MAIN_TOKEN}, json={"channel_id": GW_CHANNEL})).start()

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
