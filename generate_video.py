import asyncio
import os
import sys
import time
import requests
from playwright.async_api import async_playwright
from PIL import Image

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
    except Exception as e:
        print(f"Telegram photo error: {e}")

def send_telegram_video(video_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        if os.path.exists(video_path):
            with open(video_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": file}, timeout=120)
    except Exception as e:
        print(f"Telegram upload error: {e}")

def read_video_prompts():
    if not os.path.exists("prompts.txt"): return {}
    with open("prompts.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    video_prompts = {}
    for idx, line in enumerate(lines, start=1):
        if "|" in line:
            video_prompts[idx] = line.split("|")[1].strip()
        else:
            video_prompts[idx] = line.strip()
    return video_prompts

def crop_image_to_9_16(image_path):
    # इमेज को Reels/Shorts के साइज (9:16) में क्रॉप करने का फंक्शन
    try:
        img = Image.open(image_path)
        w, h = img.size
        target_ratio = 9 / 16
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # इमेज चौड़ी है, तो साइड से काटेंगे
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            # इमेज लंबी है, तो ऊपर-नीचे से काटेंगे
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
            
        img.save(image_path)
        print(f"✂️ Image successfully cropped to 9:16 format: {image_path}")
    except Exception as e:
        print(f"⚠️ Failed to crop image: {e}")

async def live_screenshot_monitor(page, machine_id, interval=8):
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
    
    img_name = f"Generated_Image_{machine_id}.jpg"
    img_path = os.path.join(IMAGE_DIR, img_name)

    if not os.path.exists(img_path):
        print(f"⚠️ Image {img_name} not found.")
        return

    # वीडियो बनाने से पहले इमेज को 9:16 में क्रॉप करें!
    crop_image_to_9_16(img_path)

    motion_prompt = video_prompts.get(machine_id, "Cinematic slow motion movement")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True, viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        monitor_task = asyncio.create_task(live_screenshot_monitor(page, machine_id, interval=8))

        await page.goto("https://upsampler.com/free-video-generator-no-signup", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        file_input = page.locator("input[type='file']").first
        await file_input.set_input_files(img_path)
        await asyncio.sleep(3)

        selectors = ["input[placeholder*='prompt' i]", "textarea", "input[type='text']"]
        for sel in selectors:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=2000):
                try:
                    await loc.fill(motion_prompt)
                    break
                except Exception:
                    continue

        generate_btn = page.get_by_role("button", name="Generate Video", exact=True)
        if not await generate_btn.is_visible(timeout=3000):
            generate_btn = page.locator("button:has-text('Generate')").first

        started = False
        for attempt in range(1, 10):
            if await generate_btn.is_visible(): await generate_btn.click()
            await asyncio.sleep(5)
            gpu_error = page.get_by_text("free GPUs are in high demand", exact=False)
            if await gpu_error.is_visible():
                print(f"⚠️ GPU busy, retrying...")
                await asyncio.sleep(6)
            else:
                started = True
                break

        if started:
            see_result_btn = page.locator("button:has-text('See result'), a:has-text('See result')").first
            video_element = page.locator("video:not([src*='_static'])").first
            start_time = time.time()
            video_ready = False

            while time.time() - start_time < 360:
                await asyncio.sleep(4)
                if await see_result_btn.is_visible():
                    await see_result_btn.click()
                if await video_element.count() > 0 and await video_element.is_visible():
                    video_ready = True
                    break

            if video_ready:
                await asyncio.sleep(4)
                video_filename = os.path.join(VIDEO_DIR, f"Video_{machine_id}.mp4")
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

                    print(f"✅ Video #{machine_id} Completed!")

        monitor_task.cancel()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
