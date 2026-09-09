import PIL
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import os
import sys
import time
import asyncio
import edge_tts
import requests
from playwright.async_api import async_playwright
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

IMAGE_DIR = "ai_generated_images"
VIDEO_DIR = "generated_videos"
os.makedirs(VIDEO_DIR, exist_ok=True)
PROMPT_FILE = "prompts.txt"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

async def generate_voiceover(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+10%", pitch="+2Hz")
    await communicate.save(output_file)

def read_prompts():
    if not os.path.exists(PROMPT_FILE): return {}
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    data = {}
    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if "|" in line:
            parts = line.split("|")
            data[idx] = {"image_prompt": parts[0].strip(), "vo_text": parts[1].strip()}
        else:
            data[idx] = {"image_prompt": line, "vo_text": line}
    return data

def create_dynamic_captions(text, duration):
    if not text: return []
    words = text.split()
    chunks = [' '.join(words[i:i+2]) for i in range(0, len(words), 2)]
    if not chunks: return []
    time_per_chunk = duration / len(chunks)
    text_clips = []
    current_time = 0
    for chunk in chunks:
        try:
            txt_clip = TextClip(chunk, fontsize=65, color='yellow', font="Arial-Bold", stroke_color='black', stroke_width=3)
            txt_clip = txt_clip.set_position(('center', 1500)).set_start(current_time).set_duration(time_per_chunk)
            text_clips.append(txt_clip)
        except Exception:
            pass
        current_time += time_per_chunk
    return text_clips

async def main():
    machine_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    prompts_data = read_prompts()
    
    img_path = os.path.join(IMAGE_DIR, f"Generated_Image_{machine_id}.jpg")
    if not os.path.exists(img_path): return

    scene_info = prompts_data.get(machine_id, {"image_prompt": "Cinematic slow motion", "vo_text": ""})
    motion_prompt = scene_info["image_prompt"]
    vo_text = scene_info["vo_text"]

    # 1. Edge-TTS Audio Generate karo
    voice_path = os.path.join(VIDEO_DIR, f"Voice_{machine_id}.mp3")
    if vo_text:
        await generate_voiceover(vo_text, voice_path)

    raw_video_path = os.path.join(VIDEO_DIR, f"Raw_Video_{machine_id}.mp4")

    # 2. Upsampler.com se Video Generate karo
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True, viewport={'width': 720, 'height': 1280})
        page = await context.new_page()

        await page.goto("https://upsampler.com/free-video-generator-no-signup", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        file_input = page.locator("input[type='file']").first
        await file_input.set_input_files(img_path)
        await asyncio.sleep(3)

        loc = page.locator("textarea, input[type='text']").first
        if await loc.is_visible():
            await loc.fill(motion_prompt)

        generate_btn = page.get_by_role("button", name="Generate Video", exact=True)
        if await generate_btn.is_visible():
            await generate_btn.click()

        video_element = page.locator("video:not([src*='_static'])").first
        start_time = time.time()
        video_ready = False

        while time.time() - start_time < 300:
            await asyncio.sleep(4)
            if await video_element.count() > 0 and await video_element.is_visible():
                video_ready = True
                break

        if video_ready:
            await asyncio.sleep(3)
            download_btn = page.locator("a:has-text('Download'), button:has-text('Download')").first
            video_src = await video_element.get_attribute("src")
            if await download_btn.is_visible():
                async with page.expect_download() as download_info:
                    await download_btn.click()
                download = await download_info.value
                await download.save_as(raw_video_path)
            elif video_src:
                v_data = requests.get(video_src).content
                with open(raw_video_path, "wb") as f: f.write(v_data)
        await browser.close()

    # 3. MoviePy se Original Sound Mute karke Microsoft Voice aur Captions lagao
    if os.path.exists(raw_video_path) and os.path.exists(voice_path):
        audio_clip = AudioFileClip(voice_path)
        duration = audio_clip.duration + 0.2

        video_clip = VideoFileClip(raw_video_path).subclip(0, min(duration, VideoFileClip(raw_video_path).duration))
        video_clip = video_clip.set_audio(audio_clip).resize(height=1920)

        captions = create_dynamic_captions(vo_text, duration)
        final_scene = CompositeVideoClip([video_clip] + captions).set_duration(duration)

        final_scene.write_videofile(os.path.join(VIDEO_DIR, f"Scene_{machine_id}.mp4"), fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    asyncio.run(main())
