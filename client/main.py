import secrets
import math
import time
import requests
import subprocess
import threading
import uuid
import os
import socket
import string
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

# Dictionary for word scanning
DICTIONARY = set()
DICTIONARY_LOADED = False

def load_system_dictionary():
    global DICTIONARY, DICTIONARY_LOADED
    paths = ["/usr/share/dict/words", "/usr/share/dict/american-english", "/usr/share/dict/british-english"]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    # Load words of length 5+ to ensure significance
                    DICTIONARY = {line.strip().lower() for line in f if len(line.strip()) >= 5}
                DICTIONARY_LOADED = True
                print(f"    Loaded {len(DICTIONARY)} words from {path}")
                return
            except Exception as e:
                print(f"    Error loading dictionary {path}: {e}")
    
    # Fallback to a tiny essential list if no system dict found
    if not DICTIONARY_LOADED:
        DICTIONARY = {"matrix", "glitch", "entropy", "signal", "reality", "vortex", "system"}
        print("    Warning: No system dictionary found. Using minimal fallback.")

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

def scan_for_words(bit_buffer):
    """
    Intensive bit-level scan for English words in the current buffer.
    Checks all 8 bit-shifts, inversions, and reversals.
    """
    results = set()
    # Convert bit buffer (deque of strings '0'/'1') to bytearray
    bits_str = "".join(list(bit_buffer))
    data = bytearray()
    for i in range(0, len(bits_str), 8):
        byte_str = bits_str[i:i+8]
        if len(byte_str) == 8:
            data.append(int(byte_str, 2))
    
    # Scanner variations
    def get_variations(raw_data):
        # 1. Standard
        yield raw_data
        # 2. Inverted
        yield bytes([b ^ 0xFF for b in raw_data])
        # 3. Bit-Reversed
        yield bytes([int(format(b, '08b')[::-1], 2) for b in raw_data])

    printable = set(string.ascii_letters.encode('ascii'))
    
    for base_data in get_variations(data):
        for shift in range(8):
            shifted = bytearray()
            for i in range(len(base_data) - 1):
                combined = (base_data[i] << 8) | base_data[i+1]
                shifted_byte = (combined >> (8 - shift)) & 0xFF
                shifted.append(shifted_byte)
            
            # Extract printable strings
            text = ""
            for b in shifted:
                if b in printable:
                    text += chr(b)
                else:
                    if len(text) >= 5:
                        for word in text.split():
                            if len(word) >= 5 and word.lower() in DICTIONARY:
                                results.add(word.upper())
                    text = ""
            if len(text) >= 5:
                for word in text.split():
                    if len(word) >= 5 and word.lower() in DICTIONARY:
                        results.add(word.upper())

    return list(results)

def send_notification(message, is_alert=True, test_type=None, p_value=None, detected_words=None):
    prefix = "🚨 " if is_alert else "ℹ️ "
    full_message = f"{prefix}Randomness Monitor: {message}"
    if detected_words:
        full_message += f" | WORDS: {', '.join(detected_words)}"
    
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
    if is_alert and test_type and p_value is not None:
        try:
            payload = {
                "client_id": CLIENT_ID,
                "test_type": test_type,
                "p_value": p_value,
                "detected_words": ", ".join(detected_words) if detected_words else None
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
    
    # Load dictionary for word scanning
    load_system_dictionary()
    
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
                    print(f"[{time.strftime('%H:%M:%S')}] P-Values: Monobit={p_monobit:.2e}, Runs={p_runs:.2e}")

                if p_monobit < THRESHOLD or p_runs < THRESHOLD:
                    test_type = "monobit" if p_monobit < THRESHOLD else "runs"
                    p_val = p_monobit if p_monobit < THRESHOLD else p_runs
                    
                    print(f"    Anomaly Detected (P={p_val:.2e}). Running intensive word scan...")
                    words = scan_for_words(bit_buffer)
                    
                    msg = f"GLITCH: {test_type.upper()} Detected (P={p_val:.2e})"
                    send_notification(msg, is_alert=True, test_type=test_type, p_value=p_val, detected_words=words)
                    
                    bit_buffer.clear() 

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        send_notification("Monitoring Stopped", is_alert=False)

if __name__ == "__main__":
    main()
