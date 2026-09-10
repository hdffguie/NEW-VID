import os
import subprocess
import re
import shutil

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
PROMPTS_FILE = "prompts.txt"
BGM_FILE = "bgm.mp3" 

os.makedirs(OUTPUT_DIR, exist_ok=True)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def read_story_prompts():
    story_lines = {}
    if not os.path.exists(PROMPTS_FILE): return story_lines
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, start=1):
        parts = line.split("|")
        if len(parts) >= 3: story_lines[idx] = parts[2].strip()
    return story_lines

def get_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        return float(subprocess.check_output(cmd).decode().strip())
    except Exception: return 4.0

def generate_tts(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    cmd = [
        "edge-tts", 
        "--voice", "hi-IN-MadhurNeural", 
        "--rate=+20%", "--pitch=-15Hz",
        "--text", text, 
        "--write-media", audio_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return audio_path
    except Exception: return None

def polish_and_sync_clip(input_path, output_path, index, story_text):
    audio_path = generate_tts(story_text, index) if story_text else None

    if audio_path and os.path.exists(audio_path):
        v_dur = get_duration(input_path) or 4.0
        a_dur = get_duration(audio_path) or 4.0

        v_pts_factor = a_dur / v_dur 
        fade_out_start = a_dur - 0.4  # वीडियो खत्म होने से 0.4 सेकंड पहले फेड-आउट शुरू होगा
        if fade_out_start < 0: fade_out_start = 0

        # 4K Vertical + Fade in/out
        HQ_SCALE = f"scale=2160:3840:flags=lanczos,unsharp=5:5:1.5:5:5:0.0,fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out_start:.2f}:d=0.4"

        # ध्यान दें: यहाँ ओरिजिनल वीडियो का ऑडियो म्यूट कर दिया गया है (सिर्फ 1:a मैप किया है)
        filter_complex = f"[0:v]setpts={v_pts_factor:.4f}*PTS,{HQ_SCALE}[v_scaled]"
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", filter_complex, 
               "-map", "[v_scaled]", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-c:a", "aac", output_path]
    else:
        HQ_SCALE = "scale=2160:3840:flags=lanczos,unsharp=5:5:1.5:5:5:0.0,fade=t=in:st=0:d=0.3,fade=t=out:st=3.6:d=0.4"
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", HQ_SCALE, 
               "-c:v", "libx264", "-crf", "16", "-preset", "slow", output_path]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✨ Synced, Muted Original, Faded & Polished 4K: {os.path.basename(input_path)}")
    except subprocess.CalledProcessError:
        shutil.copy(input_path, output_path)

def main():
    if not os.path.exists(INPUT_DIR): return
    story_lines = read_story_prompts()
    video_files = [os.path.join(root, f) for root, dirs, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")]

    if not video_files: return
    video_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    polished_files = []
    for idx, v_path in enumerate(video_files, start=1):
        out_path = os.path.join(OUTPUT_DIR, f"processed_{idx}.mp4")
        polish_and_sync_clip(v_path, out_path, idx, story_lines.get(idx, ""))
        polished_files.append(out_path)

    concat_list_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for p_file in polished_files:
            f.write(f"file '{os.path.basename(p_file)}'\n")

    temp_movie_path = os.path.join(OUTPUT_DIR, "Temp_Movie.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", temp_movie_path], check=True)
    final_movie_path = os.path.join(OUTPUT_DIR, "Full_Cinematic_Story.mp4")

    if os.path.exists(BGM_FILE):
        bgm_cmd = [
            "ffmpeg", "-y", "-i", temp_movie_path, "-stream_loop", "-1", "-i", BGM_FILE,
            "-filter_complex", "[1:a]volume=0.10[bgm]; [0:a][bgm]amix=inputs=2:duration=first[mixed_a]; [mixed_a]volume=1.5[final_a]",
            "-map", "0:v", "-map", "[final_a]", "-c:v", "copy", "-c:a", "aac", "-shortest", final_movie_path
        ]
        subprocess.run(bgm_cmd, check=True)
        os.remove(temp_movie_path)
    else:
        os.rename(temp_movie_path, final_movie_path)

if __name__ == "__main__":
    main()
