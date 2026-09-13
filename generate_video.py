import asyncio
import os
import sys
import time
import requests
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
VIDEO_DIR = "generated_videos"

os.makedirs(VIDEO_DIR, exist_ok=True)

def send_telegram_video(video_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        if os.path.exists(video_path):
            with open(video_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": file}, timeout=120)
    except Exception as e: pass

def read_video_prompts():
    if not os.path.exists("prompts.txt"): return {}
    with open("prompts.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    video_prompts = {}
    for idx, line in enumerate(lines, start=1):
        parts = line.strip().split("|")
        if len(parts) >= 4:
            # 🚨 जादू यहाँ है: Text-to-Video के लिए हम Character (part 2) और Action (part 3) को मिला रहे हैं!
            video_prompts[idx] = f"{parts[2].strip()}, {parts[3].strip()}"
        else:
            video_prompts[idx] = "Dark cinematic horror scene, extremely high quality, 8k"
    return video_prompts

async def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    video_prompts = read_video_prompts()
    
    super_prompt = video_prompts.get(machine_id, "Cinematic slow motion movement, high quality")
    print(f"🖥️ Machine {machine_id} processing TEXT-TO-VIDEO with Super Prompt: {super_prompt}")

    async with async_playwright() as p:
        max_browser_restarts = 5  
        
        for attempt in range(1, max_browser_restarts + 1):
            print(f"\n🔄 [Attempt {attempt}/{max_browser_restarts}] Opening Upsampler...")
            
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1280, 'height': 720})
            page = await context.new_page()

            try:
                await page.goto("https://upsampler.com/free-video-generator-no-signup", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                try:
                    accept_btn = page.get_by_role("button", name="Accept")
                    if await accept_btn.is_visible(timeout=3000): await accept_btn.click()
                except: pass

                # 🚨 यहाँ से इमेज अपलोड का कोड हटा दिया गया है। 

                # सीधा Prompt Type करेगा
                for sel in ["input[placeholder*='prompt' i]", "textarea[placeholder*='prompt' i]", "textarea"]:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        await loc.fill(super_prompt)
                        break

                # Generate Button
                generate_btn = page.get_by_role("button", name="Generate Video", exact=True)
                if not await generate_btn.is_visible(timeout=3000):
                    generate_btn = page.locator("button:has-text('Generate')").first
                
                if await generate_btn.is_visible():
                    print("🖱️ Clicking Generate button...")
                    await generate_btn.click()
                
                await asyncio.sleep(8)
                
                # एरर चेक
                gpu_error = page.get_by_text("free GPUs are in high demand", exact=False)
                ip_limit_error = page.get_by_text("used up today", exact=False)

                if await ip_limit_error.is_visible() or await gpu_error.is_visible():
                    print("⚠️ GPU Overload Error! Closing Chrome and trying again...")
                    await browser.close()
                    await asyncio.sleep(5)
                    continue

                print("✅ Generation Started! Waiting for 5 minutes...")
                see_result_btn = page.locator("button:has-text('See result'), a:has-text('See result')").first
                video_element = page.locator("video:not([src*='_static'])").first

                start_time = time.time()
                video_ready = False

                while time.time() - start_time < 300: 
                    await asyncio.sleep(5)
                    if await see_result_btn.is_visible():
                        await see_result_btn.click()
                        await asyncio.sleep(2)

                    if await video_element.count() > 0 and await video_element.is_visible():
                        video_ready = True
                        break

                if video_ready:
                    await asyncio.sleep(3)
                    video_filename = os.path.join(VIDEO_DIR, f"video_{machine_id}.mp4")
                    video_src = await video_element.get_attribute("src")

                    if video_src:
                        download_btn = page.locator("a:has-text('Download'), button:has-text('Download')").first
                        if await download_btn.is_visible():
                            async with page.expect_download() as download_info:
                                await download_btn.click()
                            download = await download_info.value
                            await download.save_as(video_filename)
                        else:
                            v_data = requests.get(video_src).content
                            with open(video_filename, "wb") as f:
                                f.write(v_data)

                        print(f"🎉 Khatarnaak Video #{machine_id} Saved!")
                        send_telegram_video(video_filename, f"🎬 Scene #{machine_id} Action Video Ready!")
                        
                        await browser.close()
                        return 

            except Exception as e:
                print(f"⚠️ Something went wrong: {e}. Restarting...")
                await browser.close()
                await asyncio.sleep(5)
                continue

        print(f"❌ Failed to generate video #{machine_id}")

if __name__ == "__main__":
    asyncio.run(main())
