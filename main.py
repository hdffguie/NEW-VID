import sys
import os
import asyncio
import requests
import re
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
SAVE_FOLDER = "bing_automated_images"
PROMPT_FILE = "prompts.txt"
os.makedirs(SAVE_FOLDER, exist_ok=True)

def send_telegram_photo(photo_path, caption=""):
    print(f"📡 Sending photo to Telegram... (Token Present: {bool(BOT_TOKEN)}, Chat ID Present: {bool(CHAT_ID)})")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram Error: BOT_TOKEN or CHAT_ID missing in environment variables!")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as file:
                res = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": file}, timeout=15)
                if res.status_code == 200:
                    print("✅ Telegram photo sent successfully!")
                else:
                    print(f"❌ Telegram API Failure: {res.status_code} - {res.text}")
        else:
            print(f"❌ Photo path not found: {photo_path}")
    except Exception as e:
        print(f"❌ Telegram Exception: {e}")

def read_prompts():
    if not os.path.exists(PROMPT_FILE):
        return {}
    prompts = {}
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f.readlines(), 1):
            parts = line.split("|")
            if len(parts) >= 3:
                prompts[idx] = parts[2].strip()
            elif len(parts) >= 1:
                prompts[idx] = parts[0].strip()
    return prompts

async def capture_and_send_screenshot(page, machine_id, step_label):
    shot_path = os.path.join(SAVE_FOLDER, f"live_status_m{machine_id}.png")
    try:
        await page.screenshot(path=shot_path)
        send_telegram_photo(shot_path, f"📸 [Machine {machine_id}] {step_label}")
    except Exception as e:
        print(f"Screenshot Error: {e}")

async def generate_single_image(machine_id, prompt_text, max_retries=3):
    out_img_path = os.path.join(SAVE_FOLDER, f"Generated_Image_{machine_id}.jpg")
    clean_prompt = re.sub(r'--ar\s+\d+:\d+', '', prompt_text).strip()

    for attempt in range(1, max_retries + 1):
        print(f"🔄 Attempt {attempt}/{max_retries} for Image #{machine_id}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # 1. Page Load
                await page.goto("https://www.bing.com/images/create/ai-image-generator", wait_until="domcontentloaded", timeout=60000)
                await capture_and_send_screenshot(page, machine_id, "Page Loaded")
                await asyncio.sleep(2)

                # 2. Input Fill
                prompt_input = page.locator("textarea, input[placeholder*='Describe'], textarea[placeholder*='Describe']").first
                await prompt_input.wait_for(state="visible", timeout=15000)
                await prompt_input.fill(clean_prompt)
                await capture_and_send_screenshot(page, machine_id, "Prompt Filled")
                await asyncio.sleep(1)

                # 3. Click Generate
                generate_btn = page.locator("button:has-text('Generate'), button:has-text('Create')").first
                if await generate_btn.is_visible(timeout=5000):
                    await generate_btn.click()
                else:
                    await prompt_input.press("Enter")

                print(f"⏳ Live monitoring started for Machine {machine_id}...")
                
                # 4. Screenshot Loop
                src = None
                for second in range(5, 95, 5):
                    await asyncio.sleep(5)
                    await capture_and_send_screenshot(page, machine_id, f"Generating... ({second}s passed)")
                    
                    img_element = page.locator("div.m_ic_img img, img[src*='th?id='], img[src*='bing.net'], div[class*='image'] img").first
                    if await img_element.is_visible():
                        src = await img_element.get_attribute("src")
                        if src and (src.startswith("http") or src.startswith("data:")):
                            print(f"🎯 Image detected at {second} seconds!")
                            break

                if not src:
                    raise Exception("Image not ready within time limit")

                img_data = requests.get(src, timeout=30).content
                with open(out_img_path, "wb") as f:
                    f.write(img_data)

                print(f"✅ Image #{machine_id} generated successfully!")
                send_telegram_photo(out_img_path, f"🎉 Final Image #{machine_id} Ready!")
                
                await browser.close()
                return True

            except Exception as e:
                print(f"⚠️ Attempt {attempt} Failed for Image {machine_id}: {e}")
                await capture_and_send_screenshot(page, machine_id, f"Error on Attempt {attempt}")
                await browser.close()
                await asyncio.sleep(3)
                
    print(f"❌ All {max_retries} attempts failed for Image #{machine_id}.")
    return False

async def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    prompts = read_prompts()
    
    prompt_text = prompts.get(machine_id, "3D Pixar animation style, cinematic lighting, 8k resolution")
    print(f"🤖 Machine {machine_id} processing IMAGE prompt ({len(prompt_text)} chars): {prompt_text}")

    success = await generate_single_image(machine_id, prompt_text, max_retries=3)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
