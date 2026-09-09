from playwright.sync_api import sync_playwright
import time
import requests
import os
import argparse
import concurrent.futures
import math
import sys
import re

SAVE_FOLDER = "ai_generated_images"
os.makedirs(SAVE_FOLDER, exist_ok=True)
PROMPT_FILE = "prompts.txt"

def download_image(url, filename):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        clean_url = url.split("?")[0]
        response = requests.get(clean_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ SAVED: {filename}")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_browser_worker(worker_id, tasks_list):
    for image_num, prompt_text in tasks_list:
        vertical_prompt = f"{prompt_text}, vertical 9:16 aspect ratio, mobile wallpaper framing"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--start-maximized"])
            context = browser.new_context(viewport={'width': 720, 'height': 1280}) 
            page = context.new_page()
            try:
                page.goto("https://www.bing.com/images/create")
                time.sleep(5) 
                search_box = page.get_by_placeholder("Describe the image you want to create")
                if not search_box.is_visible():
                    search_box = page.locator("textarea[name='q'], #sb_form_q").first
                search_box.fill(vertical_prompt)
                page.locator("button:has-text('Generate'), button:has-text('Create'), #create_btn_c").first.click()
                
                img_url = None
                for attempt in range(45):
                    time.sleep(2) 
                    all_image_srcs = page.evaluate("() => Array.from(document.querySelectorAll('img')).map(img => img.src)")
                    for src in all_image_srcs:
                        if "OIG" in src:
                            img_url = src
                            break 
                    if img_url: break 
                
                if img_url:
                    download_image(img_url, os.path.join(SAVE_FOLDER, f"Generated_Image_{image_num}.jpg"))
            except Exception as e:
                print(f"⚠️ Error Image {image_num}: {e}")
            finally:
                browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--machine_id", type=int, default=1)
    parser.add_argument("--total_machines", type=int, default=1)
    args = parser.parse_args()
    
    if not os.path.exists(PROMPT_FILE): sys.exit(1)
        
    all_prompts = []
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                clean_line = re.sub(r'^\d+[\.\-\)]?\s*', '', line)
                parts = clean_line.split('|')
                all_prompts.append(parts[0].strip())
        
    total_prompts = len(all_prompts)
    all_tasks = [(i + 1, all_prompts[i]) for i in range(total_prompts)]
    chunk_size = math.ceil(total_prompts / args.total_machines)
    start_idx = (args.machine_id - 1) * chunk_size
    end_idx = min(start_idx + chunk_size, total_prompts)
    machine_tasks = all_tasks[start_idx:end_idx]
    
    if not machine_tasks: sys.exit(0)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        mid = len(machine_tasks) // 2
        if machine_tasks[:mid]: executor.submit(run_browser_worker, 1, machine_tasks[:mid])
        if machine_tasks[mid:]: executor.submit(run_browser_worker, 2, machine_tasks[mid:])
