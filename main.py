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
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": file}, timeout=15)
    except Exception as e:
        print(f"Telegram photo error: {e}")

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
                # 1. Open Bing AI Creator
                await page.goto("https://www.bing.com/images/create/ai-image-generator", wait_until="domcontentloaded", timeout=60000)
                await capture_and_send_screenshot(page, machine_id, "Page Loaded")
                await asyncio.sleep(2)

                # 2. Fill Prompt
                prompt_input = page.locator("textarea, input[placeholder*='Describe']").first
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

                print(f"⏳ Waiting for image generation to complete on Machine {machine_id}...")
                
                # 4. "We are generating..." टेक्स्ट के गायब होने का इंतज़ार करें
                loader_text = page.locator("text='We are generating the image for you...'")
                try:
                    await loader_text.wait_for(state="detached", timeout=90000)
                    print("✅ Image generation completed (loader disappeared).")
                except Exception:
                    print("⚠️ Loader timeout or already hidden, proceeding to check download button...")

                # 5. Enabled Download Button का इंतज़ार करें
                download_btn = page.locator("button.acf-button-standard__btn[title='Download']:not([disabled]), button[title='Download']:not([disabled])").first
                
                await download_btn.wait_for(state="visible", timeout=30000)
                await capture_and_send_screenshot(page, machine_id, "Image Generated & Download Ready")

                # 6. Trigger Native Download
                async with page.expect_download(timeout=30000) as download_info:
                    await download_btn.click()
                
                download = await download_info.value
                await download.save_as(out_img_path)

                print(f"✅ Image #{machine_id} downloaded successfully!")
                send_telegram_photo(out_img_path, f"🎉 Final Image #{machine_id} Downloaded!")
                
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
