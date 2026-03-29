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
    if not is_farming: return 
    
    fast_post(token, "!work")
    time.sleep(random.uniform(1.5, 2.5)) 
    
    if not is_farming: return
    fast_post(token, "!dep all")

def farmer_loop():
    # STARTUP DELAY: Wait 120s before the first ever grind starts
    print("⏳ [SYSTEM] Script started. Waiting 120s for account recovery...")
    for _ in range(120):
        time.sleep(1)

    while True:
        try:
            if is_farming:
                FULL_SQUAD = [MAIN_TOKEN] + ALTS 
                now = datetime.now(KH_TZ).strftime('%I:%M:%S %p')
                print(f"🚀 [{now}] --- TURBO GRIND STARTING ---")
                
                threads = []
                for t in FULL_SQUAD:
                    if not is_farming: break
                    
                    thread = threading.Thread(target=worker_task, args=(t,))
                    thread.daemon = True 
                    thread.start()
                    threads.append(thread)
                
                for thread in threads:
                    thread.join(timeout=5)

                # The "Big Sleep" - Checks for .stop every 1s
                for _ in range(135):
                    if not is_farming: break
                    time.sleep(1)
                    
                if is_farming:
                    print(f"💤 Cycle finished. Restarting.")
            else:
                time.sleep(1) 
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)
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
        alt1_token = ALTS[0] # Your Coach & Banker
        
        # 🟢 1. START/STOP GRINDING
        if cmd == ".start" and is_owner:
            if not is_farming:
                # Alt 1 confirms receipt of the command
                fast_post(alt1_token, "✅ **Command Received.** Farm will resume in **2 minutes**.")
                
                # Background thread to handle the 2-minute wait
                def delayed_start():
                    global is_farming
                    time.sleep(120)  # The 2-minute recovery time
                    if is_owner: # Final check to ensure we still want to farm
                        is_farming = True
                        print(">>> System: 120s delay finished. Grinding now ACTIVE.")

                threading.Thread(target=delayed_start).start()

        elif cmd == ".stop" and is_owner:
            is_farming = False
            # Silent stop as requested
            print(">>> System: Farming Paused Silently")

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

        # 🎰 3. MAIN ACCOUNT SMART GAMBLE (.rou / .bj)
        elif is_owner and (cmd.startswith(".rou ") or cmd.startswith(".bj ")):
            try:
                parts = cmd.split(" ")
                action = parts[0]
                raw_amt = parts[1]
                
                mult = 1000 if "k" in raw_amt else 1000000 if "m" in raw_amt else 1
                clean_amt = int(re.sub(r"[^\d]", "", raw_amt)) * mult

                def run_gamble():
                    fast_post(MAIN_TOKEN, f"!with {clean_amt}")
                    time.sleep(1.2)
                    if action == ".rou":
                        side = parts[2] if len(parts) > 2 else "black"
                        fast_post(MAIN_TOKEN, f"!roulette {clean_amt} {side}")
                    else:
                        fast_post(MAIN_TOKEN, f"!blackjack {clean_amt}")
                threading.Thread(target=run_gamble).start()
            except:
                pass

    # 🧠 4. PRO ALT 1 BJ COACH (.h [Total] [Dealer] [Pair y/n])
        elif cmd.startswith(".h "):
            try:
                p = cmd.split(" ")
                my_total = int(p[1])
                dealer_up = int(p[2])
                is_pair = p[3].lower() == "y" if len(p) > 3 else False
                alt1_token = ALTS[0] 
                
                decision = "hit"
                win_prob = 40 # Default starting point

                # --- A. PROBABILITY CALCULATOR ---
                if my_total >= 20: win_prob = 92
                elif my_total == 19: win_prob = 85
                elif my_total == 18: win_prob = 77
                elif my_total == 11: win_prob = 66
                elif my_total == 10: win_prob = 58
                elif 13 <= my_total <= 16:
                    # High risk hands: better chance if dealer is 2-6 (Bust risk)
                    win_prob = 42 if dealer_up <= 6 else 21
                elif my_total <= 9:
                    win_prob = 35 # Low total, needs multiple hits
                
                # Bonus: Dealer showing a 4, 5, or 6 increases your win chance
                if 4 <= dealer_up <= 6:
                    win_prob += 10

                # --- B. SPLIT LOGIC ---
                if is_pair:
                    if my_total in [2, 12, 16]: 
                        decision = "split"
                    elif my_total in [4, 6, 14] and dealer_up <= 7: 
                        decision = "split"
                    elif my_total == 18 and dealer_up not in [7, 10, 11]: 
                        decision = "split"
                
                # --- C. DOUBLE DOWN LOGIC ---
                if decision == "hit":
                    if my_total == 11: 
                        decision = "doubledown"
                    elif my_total == 10 and dealer_up <= 9: 
                        decision = "doubledown"
                    elif my_total == 9 and 3 <= dealer_up <= 6: 
                        decision = "doubledown"

                # --- D. STAND LOGIC ---
                if decision == "hit":
                    if my_total >= 17:
                        decision = "stand"
                    elif 13 <= my_total <= 16 and dealer_up <= 6:
                        decision = "stand"
                    elif my_total == 12 and 4 <= dealer_up <= 6:
                        decision = "stand"
                
                # --- E. FINAL OUTPUT ---
                final_msg = f"**{decision.upper()}** (Win Chance: **{win_prob}%**)"
                threading.Thread(target=lambda: fast_post(alt1_token, final_msg)).start()
            except:
                pass
        # 🏦 5. BANKER COMMANDS (.da1 / .pa1)
        # Alt 1 Deposit All
        elif cmd == ".da1" and is_owner:
            threading.Thread(target=lambda: fast_post(alt1_token, "!dep all")).start()

        # Alt 1 Pay Main (Usage: .pa1 500k)
        elif cmd.startswith(".pa1 ") and is_owner:
            try:
                raw_val = cmd.split(" ")[1]
                m = 1000 if "k" in raw_val else 1000000 if "m" in raw_val else 1
                val = int(re.sub(r"[^\d]", "", raw_val)) * m
                def alt_pay():
                    fast_post(alt1_token, f"!with {val}")
                    time.sleep(1.2)
                    fast_post(alt1_token, f"!pay ayngyl1 {val}")
                threading.Thread(target=alt_pay).start()
            except:
                pass

        # 💰 6. UTILITY (.collect / .flex / .rent)
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
