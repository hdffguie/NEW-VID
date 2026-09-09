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
        print(f"📥 Downloading: {clean_url[:50]}...") 
        response = requests.get(clean_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ SAVED: {filename}")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_browser_worker(worker_id, tasks_list):
    print(f"🤖 Worker {worker_id} started! Processing {len(tasks_list)} images...")
    
    for image_num, prompt_text in tasks_list:
        # 9:16 Aspect ratio ke liye prompt ke sath keywords add kar rahe hain taaki vertical image bane
        vertical_prompt = f"{prompt_text}, vertical 9:16 aspect ratio, mobile wallpaper framing, full body portrait view"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--start-maximized"])
            # Mobile/Vertical Viewport Set kar rahe hain (9:16 ratio jaise 720x1280)
            context = browser.new_context(
                viewport={'width': 720, 'height': 1280},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            ) 
            page = context.new_page()
            try:
                page.goto("https://www.bing.com/images/create")
                time.sleep(5) 
                
                search_box = page.get_by_placeholder("Describe the image you want to create")
                if not search_box.is_visible():
                    search_box = page.locator("textarea[name='q'], #sb_form_q").first
                
                search_box.fill(vertical_prompt)
                page.locator("button:has-text('Generate'), button:has-text('Create'), button:has-text('Join'), #create_btn_c").first.click()
                
                img_url = None
                for attempt in range(45):
                    time.sleep(2) 
                    all_image_srcs = page.evaluate("() => Array.from(document.querySelectorAll('img')).map(img => img.src)")
                    for src in all_image_srcs:
                        if "OIG" in src:
                            img_url = src
                            break 
                    if img_url:
                        break 
                
                if img_url:
                    download_image(img_url, os.path.join(SAVE_FOLDER, f"Generated_Image_{image_num}.jpg"))
                else:
                    print(f"⚠️ Image nahi mili: {image_num}")
            except Exception as e:
                print(f"⚠️ Error Image {image_num}: {e}")
            finally:
                browser.close()
        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--machine_id", type=int, default=1)
    parser.add_argument("--total_machines", type=int, default=1)
    args = parser.parse_args()
    
    if not os.path.exists(PROMPT_FILE):
        sys.exit(1)
        
    all_prompts = []
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                clean_line = re.sub(r'^\d+[\.\-\)]?\s*', '', line)
                parts = clean_line.split('|')
                all_prompts.append(parts[1].strip() if len(parts) > 1 else parts[0].strip())
        
    total_prompts = len(all_prompts)
    if total_prompts == 0: sys.exit(1)

    all_tasks = [(i + 1, all_prompts[i]) for i in range(total_prompts)]
    chunk_size = math.ceil(total_prompts / args.total_machines)
    start_idx = (args.machine_id - 1) * chunk_size
    end_idx = min(start_idx + chunk_size, total_prompts)
    machine_tasks = all_tasks[start_idx:end_idx]
    
    if len(machine_tasks) == 0: sys.exit(0)
        
    mid_point = len(machine_tasks) // 2
    worker_1_tasks, worker_2_tasks = machine_tasks[:mid_point], machine_tasks[mid_point:]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        if worker_1_tasks: executor.submit(run_browser_worker, 1, worker_1_tasks)
        if worker_2_tasks: executor.submit(run_browser_worker, 2, worker_2_tasks)
