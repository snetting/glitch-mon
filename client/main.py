import secrets
import math
import time
import requests
import subprocess
import threading
import uuid
import os
import socket
from collections import deque

# --- CONFIGURATION ---
# ntfy.sh topic (Optional: Set to empty string to disable)
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "steve_random_glitch")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}" if NTFY_TOPIC else None

# Central Server Configuration
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")
CLIENT_ID = str(uuid.uuid4())

# Geolocation data
CLIENT_LOCATION = {"latitude": 0, "longitude": 0, "country": "Position Unknown", "ip_address": "Unknown"}

WINDOW_SIZE = 10000    # Increased for better statistical significance
CHECK_INTERVAL = 1      # Add new bits every 1 second
ANALYSIS_INTERVAL = 60  # Run statistical tests every 60 seconds (more independent)
THRESHOLD = 1e-6        # Much stricter p-value threshold (1 in a million)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def fetch_public_location():
    global CLIENT_LOCATION
    local_ip = get_local_ip()
    
    # Check if we are on a local/private IP
    is_local = False
    parts = local_ip.split('.')
    if len(parts) == 4:
        p1, p2 = int(parts[0]), int(parts[1])
        if p1 == 10 or (p1 == 172 and 16 <= p2 <= 31) or (p1 == 192 and p2 == 168) or p1 == 127:
            is_local = True

    if is_local:
        print(f"    Local IP detected ({local_ip}), fetching public identity...")
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            data = resp.json()
            if data.get("status") == "success":
                CLIENT_LOCATION = {
                    "latitude": data.get("lat", 0),
                    "longitude": data.get("lon", 0),
                    "country": data.get("country", "Position Unknown"),
                    "ip_address": data.get("query", "Unknown")
                }
                print(f"    Public Identity: {CLIENT_LOCATION['ip_address']} ({CLIENT_LOCATION['country']})")
        except Exception as e:
            print(f"    Failed to fetch public IP/location: {e}")

def send_notification(message, is_alert=True, test_type=None, p_value=None):
    prefix = "🚨 " if is_alert else "ℹ️ "
    full_message = f"{prefix}Randomness Monitor: {message}"
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [!] {full_message}")
    
    # 1. Local/Ntfy Notification (Optional)
    if NTFY_URL:
        try:
            requests.post(NTFY_URL, data=full_message.encode("utf-8"), timeout=5)
        except: pass

    try:
        subprocess.run(["notify-send", "Randomness Monitor", message], check=False)
    except: pass

    # 2. Central API Reporting
    if is_alert and test_type and p_value:
        try:
            payload = {
                "client_id": CLIENT_ID,
                "test_type": test_type,
                "p_value": p_value
            }
            payload.update(CLIENT_LOCATION)
            requests.post(f"{SERVER_URL}/api/report", json=payload, timeout=5)
        except Exception as e:
            print(f"    Failed to report to central server: {e}")

def heartbeat_thread():
    while True:
        try:
            payload = {"client_id": CLIENT_ID}
            payload.update(CLIENT_LOCATION)
            requests.post(f"{SERVER_URL}/api/heartbeat", json=payload, timeout=5)
        except:
            pass
        time.sleep(60) # Every minute

def monobit_test(bits):
    n = len(bits)
    s = sum(1 if b == '1' else -1 for b in bits)
    s_obs = abs(s) / math.sqrt(n)
    return math.erfc(s_obs / math.sqrt(2))

def runs_test(bits):
    n = len(bits)
    pi = sum(1 for b in bits if b == '1') / n
    if abs(pi - 0.5) >= (2 / math.sqrt(n)):
        return 0.0
    v_obs = 1 
    for i in range(n - 1):
        if bits[i] != bits[i+1]:
            v_obs += 1
    return math.erfc(abs(v_obs - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))

def main():
    # Attempt to fetch public location if on a local IP
    fetch_public_location()
    
    # Start heartbeat background thread
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    
    send_notification("Monitoring Started (Distributed Node)", is_alert=False)
    print(f"Node ID: {CLIENT_ID}")
    
    bit_buffer = deque(maxlen=WINDOW_SIZE)
    last_analysis_time = time.time()
    
    buffer_ready = False
    try:
        print(f"Waiting for buffer to fill ({WINDOW_SIZE} bits)...")
        while True:
            new_val = secrets.randbits(8)
            bits = format(new_val, '08b')
            for b in bits:
                bit_buffer.append(b)
            
            current_time = time.time()
            if len(bit_buffer) >= WINDOW_SIZE and (current_time - last_analysis_time) >= ANALYSIS_INTERVAL:
                if not buffer_ready:
                    print("Buffer full. Monitoring active.")
                    buffer_ready = True
                p_monobit = monobit_test(list(bit_buffer))
                p_runs = runs_test(list(bit_buffer))
                last_analysis_time = current_time
                
                if int(current_time) % 60 == 0:
                    print(f"[{time.strftime('%H:%M:%S')}] P-Values: Monobit={p_monobit:.4f}, Runs={p_runs:.4f}")

                if p_monobit < THRESHOLD:
                    msg = f"GLITCH: Imbalance Detected (P={p_monobit:.6f})"
                    send_notification(msg, is_alert=True, test_type="monobit", p_value=p_monobit)
                    bit_buffer.clear() 
                elif p_runs < THRESHOLD:
                    msg = f"GLITCH: Pattern Detected (P={p_runs:.6f})"
                    send_notification(msg, is_alert=True, test_type="runs", p_value=p_runs)
                    bit_buffer.clear()

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        send_notification("Monitoring Stopped", is_alert=False)

if __name__ == "__main__":
    main()
