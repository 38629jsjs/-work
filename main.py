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
# SECTION 4: PREMIUM COMMANDS & GAMBLE
# ==========================================

# Helper to send messages at maximum safe speed with jitter
def fast_post(token, content):
    url = f"https://discord.com/api/v9/channels/{ECO_CHANNEL}/messages"
    # Small jitter to stay under Discord's radar
    time.sleep(random.uniform(0.1, 0.4))
    try:
        requests.post(url, headers={"Authorization": token}, json={"content": content})
    except:
        pass

def handle_all_commands(content, author_id):
    global is_farming, rentals
    cmd = content.lower().strip()
    now_ts = time.time()
    
    # Permission Checks
    is_owner = (author_id == MAIN_ID)
    is_renter = author_id in rentals and now_ts < rentals[author_id]

    if is_owner or is_renter:
        
        # 🟢 1. START/STOP GRINDING (Only affects Auto-Farmer loop)
        if cmd == ".start" and is_owner:
            is_farming = True
            fast_post(MAIN_TOKEN, "🚀 **AUTO-GRIND STARTED**: Main + Alts are now farming.")

        elif cmd == ".stop" and is_owner:
            is_farming = False
            fast_post(MAIN_TOKEN, "🛑 **AUTO-GRIND STOPPED**: Farming paused. Manual commands ACTIVE.")

        # 🎯 2. TURBO MANUAL ROB (.rob @user 1-5)
        elif cmd.startswith(".rob "):
            try:
                parts = cmd.split(" ")
                victim = parts[1]
                idx = int(parts[2]) - 1
                if 0 <= idx < len(ALTS):
                    tok = ALTS[idx]
                    def execute_rob():
                        # Phase A: Empty Alt Wallet to your Main
                        fast_post(tok, "!with all")
                        time.sleep(1.1)
                        fast_post(tok, "!pay ayngyl1 all")
                        # Phase B: The Attack
                        time.sleep(1.1)
                        fast_post(tok, f"!rob {victim}")
                        # Phase C: Secure the Loot
                        time.sleep(2.5) 
                        fast_post(tok, "!pay ayngyl1 all")
                    threading.Thread(target=execute_rob).start()
            except:
                pass

        # 🎰 3. MAIN ACCOUNT SMART GAMBLE (.rou 7k red / .bj 5k)
        elif is_owner and (cmd.startswith(".rou ") or cmd.startswith(".bj ")):
            try:
                parts = cmd.split(" ")
                action = parts[0]
                raw_amt = parts[1]
                
                # THE CONVERTER: Handles 7k -> 7000 | 1.2m -> 1200000
                mult = 1000 if "k" in raw_amt else 1000000 if "m" in raw_amt else 1
                clean_amt = int(re.sub(r"[^\d]", "", raw_amt)) * mult

                def run_gamble():
                    fast_post(MAIN_TOKEN, f"!with {clean_amt}")
                    time.sleep(1.2)
                    if action == ".rou":
                        # Picks the color (default to black if you forget to type it)
                        side = parts[2] if len(parts) > 2 else "black"
                        fast_post(MAIN_TOKEN, f"!roulette {clean_amt} {side}")
                    else:
                        fast_post(MAIN_TOKEN, f"!blackjack {clean_amt}")
                threading.Thread(target=run_gamble).start()
            except:
                pass

        # 🧠 4. ALT 1 BJ COACH (.h [Your_Total] [Dealer_Card])
        # Usage: .h 13 5 -> Alt 1 replies "stand"
        elif cmd.startswith(".h "):
            try:
                p = cmd.split(" ")
                my_total = int(p[1])
                dealer_up = int(p[2])
                alt1_token = ALTS[0] 
                
                # CASINO BASIC STRATEGY LOGIC
                decision = "hit"
                if my_total >= 17:
                    decision = "stand"
                elif 13 <= my_total <= 16:
                    # If dealer is weak (2-6), we stand and wait for them to bust
                    if dealer_up <= 6:
                        decision = "stand"
                    else:
                        decision = "hit"
                elif my_total == 12:
                    if 4 <= dealer_up <= 6:
                        decision = "stand"
                    else:
                        decision = "hit"
                
                threading.Thread(target=lambda: fast_post(alt1_token, decision)).start()
            except:
                pass

        # 💰 5. UTILITY (.collect / .flex / .rent)
        elif cmd == ".collect":
            def collect_all(tk):
                fast_post(tk, "!with all")
                time.sleep(1.2)
                fast_post(tk, "!pay ayngyl1 all")
            for t in ALTS:
                threading.Thread(target=collect_all, args=(t,)).start()

        elif cmd == ".flex":
            for t in ALTS:
                threading.Thread(target=fast_post, args=(t, "!bal")).start()

        elif is_owner and cmd.startswith(".rent "):
            try:
                p = cmd.split(" ")
                target_user = p[1]
                hours = int(p[2])
                rentals[target_user] = now_ts + (hours * 3600)
                fast_post(MAIN_TOKEN, f"✅ **RENTAL ACTIVE**: <@{target_user}> for {hours}h.")
            except:
                pass
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
