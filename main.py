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
                await asyncio.sleep(2)

                # 2. Fill Prompt
                prompt_input = page.locator("textarea, input[placeholder*='Describe']").first
                await prompt_input.wait_for(state="visible", timeout=15000)
                await prompt_input.fill(clean_prompt)
                await asyncio.sleep(1)

                # 3. Click Generate
                generate_btn = page.locator("button:has-text('Generate'), button:has-text('Create')").first
                if await generate_btn.is_visible(timeout=5000):
                    await generate_btn.click()
                else:
                    await prompt_input.press("Enter")

                print(f"⏳ Waiting for Download button to appear on Machine {machine_id}...")
                
                # 4. Download Button Selector (Arrow Icon at bottom)
                download_btn = page.locator("button[title*='Download'], a[title*='Download'], svg[class*='download']").first
                
                # अगर विशेष एट्रीब्यूट न मिले तो लेआउट के डाउनलोड आइकन पर सीधे क्लिक करें
                if not await download_btn.is_visible(timeout=75000):
                    download_btn = page.locator("button:has(svg), div:has-text('Set as Wallpaper') ~ button, div:has-text('Edit image') ~ button").first

                await download_btn.wait_for(state="visible", timeout=15000)

                # 5. Native Download Trigger
                async with page.expect_download(timeout=30000) as download_info:
                    await download_btn.click()
                
                download = await download_info.value
                await download.save_as(out_img_path)

                print(f"✅ Image #{machine_id} downloaded successfully using Download Button!")
                send_telegram_photo(out_img_path, f"🎉 Image #{machine_id} Downloaded!")
                
                await browser.close()
                return True

            except Exception as e:
                print(f"⚠️ Direct download button attempt failed ({e}). Trying fallback HTTP fetch...")
                try:
                    # Fallback: बड़ी मुख्य इमेज से src निकालकर डायरेक्ट HTTP गेट करना
                    main_img = page.locator("div[class*='main'] img, img[src*='th?id='], img[src*='bing.net']").first
                    if await main_img.is_visible(timeout=10000):
                        src = await main_img.get_attribute("src")
                        if src and (src.startswith("http") or src.startswith("data:")):
                            img_data = requests.get(src, timeout=30).content
                            with open(out_img_path, "wb") as f:
                                f.write(img_data)
                            print(f"✅ Image #{machine_id} fetched via fallback HTTP!")
                            send_telegram_photo(out_img_path, f"🎉 Image #{machine_id} Ready!")
                            await browser.close()
                            return True
                except Exception as fb_err:
                    print(f"Fallback error: {fb_err}")

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
