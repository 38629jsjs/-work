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
# SECTION 2: HYBRID RECOVERY (SPEED + SAFETY)
# ==========================================

def alt_worker_task(token, run_illegal):
    """ALTS: !slut + !crime together (Zero-Fine) -> !work -> Final Pay"""
    if not is_farming: return 
    
    # 1. THE SIMULTANEOUS RISK (Zero-Fine Shield)
    # Firing these together while the wallet is empty means fines = $0.
    if run_illegal:
        fast_post(token, "!slut")
        fast_post(token, "!crime")
        
        # Wait for both risky results to process (4 seconds)
        # We don't pay yet to keep the script fast and clean
        time.sleep(4.0)

    # 2. THE GUARANTEED INCOME (Work)
    # Done after the risks so this money is NEVER touched by a crime fine.
    fast_post(token, "!work")
    
    # Give the bot time to process the Work salary
    time.sleep(random.uniform(2.0, 3.0))
    
    # 3. THE FINAL CLEARANCE
    # Pay everything (Work + Slut + Crime winnings) in ONE transaction.
    # This reduces spam and stays under the radar.
    fast_post(token, f"!pay ayngyl1 all")

def main_banker_task():
    """MAIN: Only safe work and locks the vault"""
    if not is_farming: return
    
    # Banker only works - 100% safe
    fast_post(MAIN_TOKEN, "!work")
    
    # Wait for all Alts to finish their simultaneous moves (25s total)
    time.sleep(25)
    
    # Lock the total profit into the Bank
    fast_post(MAIN_TOKEN, "!dep all")

def farmer_loop():
    print("⏳ [SYSTEM] Simultaneous Risk Engine Active. 10m CD for Risky Commands.")
    # Initial startup delay
    time.sleep(120) 
    
    cycle_count = 0
    while True:
        try:
            if is_farming:
                # 10 MINUTE COOLDOWN LOGIC:
                # 125s cycle * 5 cycles = 10.4 minutes. Safely resets !crime/!slut.
                run_illegal = (cycle_count % 5 == 0)
                
                now = datetime.now(KH_TZ).strftime('%I:%M:%S %p')
                mode = "🔥 FULL GRIND (Risks On)" if run_illegal else "🛡️ SAFE WORK"
                print(f"🚀 [{now}] Cycle {cycle_count} | {mode}")
                
                threads = []
                # Start all Alts in parallel
                for t in ALTS:
                    th = threading.Thread(target=alt_worker_task, args=(t, run_illegal))
                    th.start()
                    threads.append(th)
                
                # Start the Banker in parallel
                m_th = threading.Thread(target=main_banker_task)
                m_th.start()
                threads.append(m_th)
                
                # Wait for all threads to finish their work
                for th in threads:
                    th.join(timeout=35)

                cycle_count += 1
                
                # The "Big Sleep" until !work cooldown (120s)
                for _ in range(125):
                    if not is_farming: break
                    time.sleep(1)
            else:
                time.sleep(1)
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
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

   # 🧠 4. PRO COACH (Tension + Every Probability)
        # Usage: .h [Total] [Dealer] [Pair y/n] [CardCount]
        elif cmd.startswith(".h "):
            try:
                p = cmd.split(" ")
                my_t = int(p[1])
                d_u = int(p[2])
                is_p = (p[3].lower() == "y") if len(p) > 3 else False
                count = int(p[4]) if len(p) > 4 else 2
                alt1_token = ALTS[0] 

                # --- 1. PROBABILITY MATRIX (Every Hand) ---
                win = 40
                if my_t >= 20: win = 92
                elif my_t == 19: win = 85
                elif my_t == 18: win = 77
                elif my_t == 17: win = 62
                elif my_t == 11: win = 66
                elif my_t == 10: win = 58
                elif my_t == 9: win = 48
                elif 13 <= my_t <= 16:
                    win = 42 if d_u <= 6 else 21
                elif my_t == 12:
                    win = 35 if d_u <= 6 else 18
                elif my_t <= 8:
                    win = 25

                # --- 2. DECK TENSION & DEALER ADJUSTMENTS ---
                # Tension Penalty: -8% win chance for every card drawn after the first 2
                tension_penalty = (count - 2) * 8
                if 4 <= d_u <= 6: win += 10  # Dealer Weak
                if d_u >= 10: win -= 10      # Dealer Strong
                win = max(1, min(99, win - tension_penalty))

                # --- 3. DECISION LOGIC ---
                decision = "HIT"
                
                # Split Logic
                if is_p:
                    if my_t in [2, 12, 16]: decision = "SPLIT"
                    elif my_t in [4, 6, 14] and d_u <= 7: decision = "SPLIT"
                    elif my_t == 18 and d_u not in [7, 10, 11]: decision = "SPLIT"
                
                # Double Down / Stand Logic
                if decision == "HIT":
                    if my_t == 11: decision = "DOUBLEDOWN"
                    elif my_t == 10 and d_u <= 9: decision = "DOUBLEDOWN"
                    elif my_t == 9 and 3 <= d_u <= 6: decision = "DOUBLEDOWN"
                    
                    if decision == "HIT":
                        if my_t >= 17: decision = "STAND"
                        elif 13 <= my_t <= 16 and d_u <= 6: decision = "STAND"
                        elif my_t == 12 and 4 <= d_u <= 6: decision = "STAND"
                        # SAFETY RULE: If Tension is high (4+ cards), Stand on 15/16
                        if count >= 4 and 15 <= my_t <= 16: decision = "STAND"

                # --- 4. OUTPUT ---
                tension_warn = " [⚠️]" if count >= 4 else ""
                final_msg = f"**{decision}** (Win: **{win}%**){tension_warn}"
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
