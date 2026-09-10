import os
import sys
import time
import re
from playwright.sync_api import sync_playwright
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
SAVE_FOLDER = "bing_automated_images"
PROMPT_FILE = "prompts.txt"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def send_telegram_photo(photo_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": file}, timeout=15)
    except Exception: pass

def download_image(url, filename):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024): f.write(chunk)
            return True
    except: return False
    return False

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

    # सिर्फ अपनी मशीन के नंबर वाला प्रॉम्प्ट उठाएगा
    line = lines[machine_id - 1]
    prompt_text = line.split("|")[0].strip()
    prompt_text = re.sub(r'^\d+[\.\-\)]?\s*', '', prompt_text) 

    print(f"🤖 Machine {machine_id} processing prompt: {prompt_text}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--start-maximized"])
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        try:
            page.goto("https://www.bing.com/images/create", timeout=60000)
            time.sleep(3)
            
            search_box = page.get_by_placeholder("Describe the image you want to create")
            if not search_box.is_visible():
                search_box = page.locator("textarea[name='q'], #sb_form_q, textarea, input[type='text']").first
            
            search_box.fill(prompt_text)
            time.sleep(1)
            
            generate_btn = page.locator("button:has-text('Generate'), button:has-text('Create'), #create_btn_div, #create_btn_c").first
            generate_btn.click()
            
            img_url = None
            for attempt in range(45):
                time.sleep(2)
                all_images = page.evaluate("""() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    return imgs.map(img => img.src).filter(src => src && (
                        src.includes('th?id=') || src.includes('OIG') || src.includes('bing.net') || src.includes('tse')
                    ));
                }""")
                for src in all_images:
                    if "logo" not in src.lower() and "icon" not in src.lower():
                        img_url = src
                        break
                if img_url: break
            
            if img_url:
                filepath = os.path.join(SAVE_FOLDER, f"Generated_Image_{machine_id}.jpg")
                if download_image(img_url, filepath):
                    print(f"✅ Success: Image {machine_id}")
                else:
                    raise Exception("Download failed")
            else:
                raise Exception("Image URL not found after generation (Possibly CAPTCHA blocked)")
                
        except Exception as e:
            print(f"⚠️ Error for Image {machine_id}: {e}")
            err_shot = os.path.join(SAVE_FOLDER, f"ERROR_Image_{machine_id}.png")
            page.screenshot(path=err_shot)
            send_telegram_photo(err_shot, f"❌ Image #{machine_id} Failed")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
