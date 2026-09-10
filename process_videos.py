import os
import subprocess
import re
import shutil

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
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
    # 🎤 एकदम क्लियर और पतली सिनेमैटिक आवाज़ (Swara)
    cmd = [
        "edge-tts", "--voice", "hi-IN-SwaraNeural", 
        "--rate=+5%", "--pitch=+12Hz", 
        "--text", text, "--write-media", audio_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def process_single_clip(input_path, output_path, index, story_text):
    audio_path = generate_tts(story_text, index) if story_text else None
    
    # 🎥 4K Vertical + 30fps फिक्स (ताकि क्रॉसफ़ेड में एरर न आए)
    HQ_SCALE = "scale=2160:3840:flags=lanczos,unsharp=5:5:1.5:5:5:0.0,fps=30"

    if audio_path and os.path.exists(audio_path):
        v_dur = get_duration(input_path)
        a_dur = get_duration(audio_path)
        v_pts_factor = (a_dur / v_dur) if v_dur > 0 else 1
        
        # ओरिजिनल साउंड इफ़ेक्ट (20% वॉल्यूम) और AI आवाज़ (150% वॉल्यूम) को मिक्स किया है
        filter_complex = (
            f"[0:v]setpts={v_pts_factor:.4f}*PTS,{HQ_SCALE}[v_out]; "
            f"[0:a]volume=0.2[orig_a]; [1:a]volume=1.5[tts_a]; "
            f"[orig_a][tts_a]amix=inputs=2:duration=longest:weights=1 1[a_out]"
        )
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", filter_complex,
               "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", output_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", HQ_SCALE, "-c:v", "libx264", "-crf", "18", "-preset", "fast", output_path]
    
    subprocess.run(cmd, check=True)
    return output_path

def merge_with_crossfade(clips):
    if not clips: return None
    merged_video = clips[0]
    
    for i in range(1, len(clips)):
        next_video = clips[i]
        dur1 = get_duration(merged_video)
        offset = max(0, dur1 - 1.0) # 1 सेकंड का ओवरलैप (एक के ऊपर एक)
        
        temp_out = os.path.join(OUTPUT_DIR, f"temp_merge_{i}.mp4")
        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration=1:offset={offset}[v_out]; "
            f"[0:a][1:a]amix=inputs=2:duration=longest[a_out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", merged_video, "-i", next_video, 
            "-filter_complex", filter_complex, 
            "-map", "[v_out]", "-map", "[a_out]", 
            "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", temp_out
        ]
        subprocess.run(cmd, check=True)
        merged_video = temp_out
        print(f"🔄 Crossfaded Clip {i+1}")
        
    return merged_video

def main():
    prompts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 3: prompts[idx] = parts[2].strip()

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    
    processed_clips = []
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, prompts.get(idx, ""))
        processed_clips.append(out_path)

    print("🎬 Starting Crossfade Merging...")
    final_merged = merge_with_crossfade(processed_clips)
    
    if final_merged:
        final_dest = os.path.join(OUTPUT_DIR, "Final_Cinematic_Movie.mp4")
        os.rename(final_merged, final_dest)
        print("🎉 Movie Ready with Crossfade!")

if __name__ == "__main__":
    main()
