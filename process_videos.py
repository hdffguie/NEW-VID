import os
import subprocess
import re

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"

# 👈 यहाँ अपने चैनल का नाम लिखें
WATERMARK_TEXT = "YOUR CHANNEL NAME" 

os.makedirs(OUTPUT_DIR, exist_ok=True)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        return float(subprocess.check_output(cmd).decode().strip())
    except: return 4.0

def generate_tts(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    cmd = [
        "edge-tts", "--voice", "hi-IN-SwaraNeural", 
        "--rate=+6%", "--pitch=+10Hz", 
        "--text", text, "--write-media", audio_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def process_single_clip(input_path, output_path, index, total_clips, story_text):
    audio_path = generate_tts(story_text, index) if story_text else None
    
    # 🌟 4K + Visual Fingerprint Color Filter + Center Watermark
    base_filter = (
        f"scale=2160:3840:flags=lanczos,"
        f"eq=contrast=1.05:saturation=1.1,"  # Color Grading (Originality)
        f"unsharp=5:5:1.5:5:5:0.0,fps=30,"
        f"drawtext=text='{WATERMARK_TEXT}':fontcolor=white@0.25:fontsize=110:x=(w-text_w)/2:y=(h-text_h)/2" # Watermark
    )

    # 🧲 Retention Booster 1: पहली क्लिप पर टॉप हुक (0-3 सेक)
    if index == 1:
        base_filter += ":drawtext=text='अंत तक जरूर देखना 😱':fontcolor=yellow:fontsize=120:x=(w-text_w)/2:y=350:enable='between(t,0,3)'"
    
    # 🧲 Retention Booster 2: आखिरी क्लिप पर Subscribe CTA
    if index == total_clips:
        base_filter += ":drawtext=text='लाइक और सब्सक्राइब करें 👇':fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=20:fontsize=100:x=(w-text_w)/2:y=h-450"

    if audio_path and os.path.exists(audio_path):
        v_dur = get_duration(input_path)
        a_dur = get_duration(audio_path)
        v_pts_factor = (a_dur / v_dur) if v_dur > 0 else 1
        
        filter_complex = (
            f"[0:v]setpts={v_pts_factor:.4f}*PTS,{base_filter}[v_out]; "
            f"[0:a]volume=0.15[orig_a]; [1:a]volume=1.6[tts_a]; " # Audio Ducking (BGM 15%, Voice 160%)
            f"[orig_a][tts_a]amix=inputs=2:duration=longest:weights=1 1[a_out]"
        )
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", filter_complex,
               "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", output_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", base_filter, "-c:v", "libx264", "-crf", "16", "-preset", "fast", output_path]
    
    subprocess.run(cmd, check=True)
    return output_path

def merge_with_crossfade(clips):
    if not clips: return None
    merged_video = clips[0]
    
    for i in range(1, len(clips)):
        next_video = clips[i]
        dur1 = get_duration(merged_video)
        offset = max(0, dur1 - 0.8) # 0.8-second smooth crossfade
        
        temp_out = os.path.join(OUTPUT_DIR, f"temp_merge_{i}.mp4")
        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration=0.8:offset={offset}[v_out]; "
            f"[0:a][1:a]amix=inputs=2:duration=longest[a_out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", merged_video, "-i", next_video, 
            "-filter_complex", filter_complex, 
            "-map", "[v_out]", "-map", "[a_out]", 
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", temp_out
        ]
        subprocess.run(cmd, check=True)
        merged_video = temp_out
        
    return merged_video

def main():
    prompts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 3: prompts[idx] = parts[2].strip()

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    
    total_clips = len(video_files)
    processed_clips = []
    
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, total_clips, prompts.get(idx, ""))
        processed_clips.append(out_path)

    print("🎬 Merging with Smooth Crossfade Transitions...")
    final_merged = merge_with_crossfade(processed_clips)
    
    if final_merged:
        final_dest = os.path.join(OUTPUT_DIR, "Final_4K_Monetizable_Short.mp4")
        os.rename(final_merged, final_dest)
        print("🎉 4K Video Ready for YouTube Upload!")

if __name__ == "__main__":
    main()
