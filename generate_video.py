import os
import sys
import subprocess
from playwright.sync_api import sync_playwright
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
SAVE_FOLDER = "generated_videos"
IMAGE_FOLDER = "bing_automated_images"
PROMPT_FILE = "prompts.txt"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def send_telegram_msg(text):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=15)
    except: pass

def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    if not os.path.exists(PROMPT_FILE):
        print("❌ prompts.txt not found!")
        sys.exit(1)

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if machine_id > len(lines) or machine_id < 1:
        print("❌ Invalid machine_id")
        sys.exit(1)

    line = lines[machine_id - 1]
    parts = line.split("|")
    
    # 🎥 Index 3 से Full Video Prompt उठाएगा (जिसमें Master Audio Prompt भी है)
    if len(parts) >= 4:
        prompt_text = parts[3].strip()
    elif len(parts) >= 3:
        prompt_text = parts[2].strip()
    else:
        prompt_text = parts[0].strip()

    img_path = os.path.join(IMAGE_FOLDER, f"Generated_Image_{machine_id}.jpg")
    out_video_path = os.path.join(SAVE_FOLDER, f"video_{machine_id}.mp4")

    print(f"🎥 Machine {machine_id} processing VIDEO prompt: {prompt_text}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            if os.path.exists(img_path):
                cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path, "-c:v", "libx264", "-t", "4", "-pix_fmt", "yuv420p", out_video_path]
                subprocess.run(cmd, check=True)
                print(f"✅ Video {machine_id} created successfully!")
            else:
                raise Exception(f"Input image Generated_Image_{machine_id}.jpg not found")
        except Exception as e:
            print(f"⚠️ Error creating video {machine_id}: {e}")
            send_telegram_msg(f"❌ Video #{machine_id} Failed: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
