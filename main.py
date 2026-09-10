import sys
import os
import asyncio
import requests
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

async def generate_single_image(machine_id, prompt_text, max_retries=4):
    out_img_path = os.path.join(SAVE_FOLDER, f"Generated_Image_{machine_id}.jpg")
    
    for attempt in range(1, max_retries + 1):
        print(f"🔄 Attempt {attempt}/{max_retries} for Image #{machine_id}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1280, 'height': 720})
            page = await context.new_page()
            
            try:
                # Bing / Image Creator Site URL
                await page.goto("https://www.bing.com/images/create", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Search/Prompt input fill
                prompt_input = page.locator("input[name='q'], textarea[name='q']").first
                if await prompt_input.is_visible(timeout=5000):
                    await prompt_input.fill(prompt_text)
                    await asyncio.sleep(1)

                create_btn = page.locator("#create_btn_div, button:has-text('Create'), a:has-text('Create')").first
                if await create_btn.is_visible(timeout=5000):
                    await create_btn.click()
                else:
                    await prompt_input.press("Enter")

                print(f"⏳ Waiting for image generation on Machine {machine_id}...")
                
                # Image element waiting
                img_element = page.locator("div.img_pt img, m_ic_img img, img.mimg").first
                await img_element.wait_for(state="visible", timeout=90000)
                
                src = await img_element.get_attribute("src")
                if not src or not src.startswith("http"):
                    raise Exception("Image URL invalid or not found")

                img_data = requests.get(src, timeout=30).content
                with open(out_img_path, "wb") as f:
                    f.write(img_data)

                print(f"✅ Image #{machine_id} generated successfully on Attempt {attempt}!")
                send_telegram_photo(out_img_path, f"🖼️ Image #{machine_id} Ready!")
                
                await browser.close()
                return True

            except Exception as e:
                print(f"⚠️ Attempt {attempt} Failed for Image {machine_id}: {e}")
                await browser.close() # Clean Cut Chrome / Close Browser
                await asyncio.sleep(5) # Fresh start gap
                
    print(f"❌ All {max_retries} attempts failed for Image #{machine_id}.")
    return False

async def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    prompts = read_prompts()
    
    prompt_text = prompts.get(machine_id, "3D Pixar animation style, cinematic lighting, 8k resolution")
    print(f"🤖 Machine {machine_id} processing IMAGE prompt ({len(prompt_text)} chars): {prompt_text}")

    success = await generate_single_image(machine_id, prompt_text, max_retries=4)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
