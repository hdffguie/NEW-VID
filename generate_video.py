import asyncio
import os
import sys
import time
import requests
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
IMAGE_DIR = "bing_automated_images"
VIDEO_DIR = "generated_videos"

os.makedirs(VIDEO_DIR, exist_ok=True)

def send_telegram_photo(photo_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": file}, timeout=15)
    except Exception as e: pass

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
            video_prompts[idx] = parts[3].strip()
        elif len(parts) >= 2:
            video_prompts[idx] = parts[1].strip()
        else:
            video_prompts[idx] = line.strip()
    return video_prompts

async def live_screenshot_monitor(page, machine_id, interval=15):
    shot_count = 1
    while True:
        try:
            await asyncio.sleep(interval)
            shot_path = f"live_video_m{machine_id}.png"
            await page.screenshot(path=shot_path)
            send_telegram_photo(shot_path, f"🎬 Machine {machine_id} Live Status #{shot_count}")
            shot_count += 1
        except asyncio.CancelledError:
            break
        except Exception:
            pass

async def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    video_prompts = read_video_prompts()
    
    if not os.path.exists(IMAGE_DIR):
        print("❌ Image directory not found!")
        return

    img_name = f"Generated_Image_{machine_id}.jpg"
    img_path = os.path.join(IMAGE_DIR, img_name)

    if not os.path.exists(img_path):
        print(f"⚠️ Image {img_name} not found for Machine {machine_id}.")
        return

    motion_prompt = video_prompts.get(machine_id, "Cinematic slow motion movement, high quality")
    print(f"🖥️ Machine {machine_id} processing Video #{machine_id} with Prompt: {motion_prompt}")

    async with async_playwright() as p:
        max_browser_restarts = 20  # 20 बार नया क्रोम खोलकर ट्राई करेगा
        
        for attempt in range(1, max_browser_restarts + 1):
            print(f"\n🔄 [Attempt {attempt}/{max_browser_restarts}] Launching a FRESH CHROME browser...")
            
            # हर बार एक बिल्कुल नया ब्राउज़र (Fresh Cache & Cookies) खुलेगा
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True, viewport={'width': 1280, 'height': 720})
            page = await context.new_page()

            monitor_task = asyncio.create_task(live_screenshot_monitor(page, machine_id, interval=20))

            try:
                await page.goto("https://upsampler.com/free-video-generator-no-signup", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Accept cookies button if it appears
                try:
                    accept_btn = page.get_by_role("button", name="Accept")
                    if await accept_btn.is_visible(timeout=3000):
                        await accept_btn.click()
                except: pass

                # इमेज अपलोड करना
                file_input = page.locator("input[type='file']").first
                await file_input.set_input_files(img_path)
                await asyncio.sleep(4)

                # प्रॉम्प्ट टाइप करना
                selectors = ["input[placeholder*='prompt' i]", "textarea[placeholder*='prompt' i]", "textarea"]
                for sel in selectors:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        try:
                            await loc.fill(motion_prompt)
                            break
                        except: continue

                # 5 सेकंड सेलेक्ट करना
                try:
                    duration_dropdown = page.get_by_text("3 seconds")
                    if await duration_dropdown.is_visible(timeout=2000):
                        await duration_dropdown.click()
                        await asyncio.sleep(1)
                        await page.get_by_text("5 seconds", exact=True).click()
                except: pass

                # Generate बटन दबाना
                generate_btn = page.get_by_role("button", name="Generate Video", exact=True)
                if not await generate_btn.is_visible(timeout=3000):
                    generate_btn = page.locator("button:has-text('Generate')").first
                
                if await generate_btn.is_visible():
                    print("🖱️ Clicking Generate button...")
                    await generate_btn.click()
                
                # एरर चेक करने के लिए 8 सेकंड रुकना
                await asyncio.sleep(8)
                
                gpu_error = page.get_by_text("free GPUs are in high demand", exact=False)
                ip_limit_error = page.get_by_text("used up today", exact=False)

                if await ip_limit_error.is_visible():
                    print(f"❌ Daily IP Limit reached! Cannot generate more videos today on Machine {machine_id}.")
                    monitor_task.cancel()
                    await browser.close()
                    return  # पूरा प्रोग्राम रोक देगा

                if await gpu_error.is_visible():
                    print("⚠️ Server is busy (GPU Error). CLOSING Chrome and trying again...")
                    monitor_task.cancel()
                    await browser.close()  # क्रोम को जड़ से बंद कर देगा
                    await asyncio.sleep(5) # 5 सेकंड रुककर अगला नया क्रोम खोलेगा
                    continue  # लूप को शुरू से स्टार्ट करेगा (नए क्रोम के साथ)

                # अगर कोई एरर नहीं आया, मतलब वीडियो बनना शुरू हो गया!
                print("✅ Generation Started Successfully! Waiting for video to process...")
                see_result_btn = page.locator("button:has-text('See result'), a:has-text('See result')").first
                video_element = page.locator("video:not([src*='_static'])").first

                start_time = time.time()
                video_ready = False

                while time.time() - start_time < 400: # 6-7 मिनट इंतज़ार करेगा
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

                        print(f"🎉 Video #{machine_id} Saved successfully as {video_filename}!")
                        send_telegram_video(video_filename, f"🎬 Scene #{machine_id} Video Ready!")
                        
                        monitor_task.cancel()
                        await browser.close()
                        return  # वीडियो बन गई, तो लूप से बाहर आ जाओ

            except Exception as e:
                print(f"⚠️ Something went wrong: {e}. Restarting Chrome...")
                monitor_task.cancel()
                await browser.close()
                await asyncio.sleep(5)
                continue

        print(f"❌ Failed to generate video #{machine_id} after {max_browser_restarts} fresh Chrome restarts.")

if __name__ == "__main__":
    asyncio.run(main())
