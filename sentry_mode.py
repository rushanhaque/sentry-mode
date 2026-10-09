import serial.tools.list_ports
import pyautogui
import time
import winsound
import json
import urllib.request
import sys
import os

# --- CONFIGURATION ---
# 1. Create a Discord Server -> Channel Settings -> Integrations -> Webhooks
# 2. Copy the Webhook URL and set it as an environment variable, never in the code:
#      setx DISCORD_WEBHOOK_URL "<your webhook url>"   (then reopen the terminal)
# If it is not set, it will just use the Sound Alarm.
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

MODE_DISARMED = "DISARMED"
MODE_ARMED    = "ARMED"
MODE_ALARM    = "ALARM_TRIGGERED"

def find_arduino():
    """Checks if the safety key is plugged in."""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p.description or "CH340" in p.description:
            return True
    return False

def send_discord_alert():
    """Sends a notification to your phone via Discord."""
    if not DISCORD_WEBHOOK_URL:
        return

    data = {
        "content": "@everyone 🚨 **SECURITY ALERT** 🚨\nUnauthorized movement detected on your PC!"
    }
    
    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL, 
            data=json.dumps(data).encode('utf-8'),
            headers={'User-Agent': 'SentryBot', 'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("[!] Notification sent to Discord/Phone.")
    except Exception as e:
        print(f"[x] Failed to send notification: {e}")

def main():
    current_mode = MODE_DISARMED
    last_mouse_pos = pyautogui.position()
    
    print("------------------------------------------------")
    print("      SENTRY MODE: ANTI-INTERFERENCE SYSTEM     ")
    print("------------------------------------------------")
    print("[*] STATUS: DISARMED. (Safety Key Detected)")
    print("[i] INSTRUCTIONS: Unplug your Arduino to ARM the system. Plug it back in to DISARM.")

    while True:
        has_key = find_arduino()
        
        # STATE MACHINE
        if current_mode == MODE_DISARMED:
            if not has_key:
                print("[!] KEY REMOVED. Arming in 3 seconds...")
                time.sleep(3)
                current_mode = MODE_ARMED
                last_mouse_pos = pyautogui.position()
                print("[*] SYSTEM ARMED. Don't touch the mouse!")
                
        elif current_mode == MODE_ARMED:
            if has_key:
                print("[*] KEY DETECTED. Disarming system...")
                current_mode = MODE_DISARMED
            else:
                # CHECK FOR MOVEMENT
                current_pos = pyautogui.position()
                # We allow a tiny bit of jitter (2 pixels) just in case
                if abs(current_pos[0] - last_mouse_pos[0]) > 5 or abs(current_pos[1] - last_mouse_pos[1]) > 5:
                    print("[!!!] MOVEMENT DETECTED [!!!]")
                    current_mode = MODE_ALARM
                    send_discord_alert()

        elif current_mode == MODE_ALARM:
            if has_key:
                print("[*] KEY DETECTED. Disarming system...")
                current_mode = MODE_DISARMED
            else:
                # SCREAM
                print("!!! ALARM !!!")
                # Two-tone emergency siren
                winsound.Beep(2500, 250)
                winsound.Beep(1500, 250)

        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[x] Exiting...")
