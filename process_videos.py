import os
import subprocess
import re

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
WATERMARK_TEXT = "YOUR CHANNEL NAME" 
ASPECT_RATIO = os.getenv("ASPECT_RATIO", "9:16")
FONT_PATH = "NotoSansHindi.ttf"  # यह वो फॉन्ट है जो हमने डाउनलोड करवाया है

os.makedirs(OUTPUT_DIR, exist_ok=True)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        return float(subprocess.check_output(cmd).decode().strip())
    except: return 4.0

def has_audio_stream(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", file_path]
        output = subprocess.check_output(cmd).decode().strip()
        return len(output) > 0
    except: return False

def generate_tts(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    cmd = ["edge-tts", "--voice", "hi-IN-MadhurNeural", "--rate=+4%", "--pitch=-2Hz", "--text", text, "--write-media", audio_path]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def process_single_clip(input_path, output_path, index, total_clips, story_text, fact_text):
    audio_path = generate_tts(story_text, index) if story_text else None
    
    # 🎯 FIX 1: अब वीडियो 'खिंचेगा' नहीं! यह स्मार्ट तरीके से क्रॉप (Crop) होगा।
    scale_filter = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840"
    font_size = 90

    # 🎯 FIX 2: वॉटरमार्क और कलर करेक्शन
    base_filter = (
        f"{scale_filter},eq=contrast=1.05:saturation=1.1,fps=30,"
        f"drawtext=text='{WATERMARK_TEXT}':fontcolor=white@0.30:fontsize={font_size}:x=(w-text_w)/2:y=(h-text_h)/2"
    )

    # 🎯 FIX 3: हिंदी टेक्स्ट डब्बे नहीं बनेंगे! फॉन्ट ऐड कर दिया गया है।
    if index == 1:
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='अंत तक जरूर देखना':fontcolor=yellow:fontsize=120:x=(w-text_w)/2:y=350:enable='between(t,0,3)'"
    
    # 🎯 FIX 4: यहाँ स्क्रीन पर मोनेटाइजेशन वाला "Fact" (तथ्य) पॉप-अप होगा!
    if fact_text:
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='Fact\: {fact_text}':fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=25:fontsize=75:x=(w-text_w)/2:y=h-600"

    v_has_audio = has_audio_stream(input_path)

    if audio_path and os.path.exists(audio_path):
        v_dur = get_duration(input_path)
        a_dur = get_duration(audio_path)
        v_pts_factor = (a_dur / v_dur) if v_dur > 0 else 1
        
        if v_has_audio:
            filter_complex = f"[0:v]setpts={v_pts_factor:.4f}*PTS,{base_filter}[v_out]; [0:a]volume=0.1[orig_a]; [1:a]volume=1.6[tts_a]; [orig_a][tts_a]amix=inputs=2[a_out]"
            cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", filter_complex, "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", "-c:a", "aac", output_path]
        else:
            filter_complex = f"[0:v]setpts={v_pts_factor:.4f}*PTS,{base_filter}[v_out]"
            cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", filter_complex, "-map", "[v_out]", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", "-c:a", "aac", output_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", base_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", output_path]
    
    subprocess.run(cmd, check=True)
    return output_path

def merge_with_crossfade(clips):
    if not clips: return None
    merged = clips[0]
    for i in range(1, len(clips)):
        next_v = clips[i]
        offset = max(0, get_duration(merged) - 0.8)
        tmp = os.path.join(OUTPUT_DIR, f"temp_{i}.mp4")
        
        if has_audio_stream(merged) and has_audio_stream(next_v):
            fc = f"[0:v][1:v]xfade=transition=fade:duration=0.8:offset={offset}[v_out]; [0:a][1:a]acrossfade=d=0.8[a_out]"
            cmd = ["ffmpeg", "-y", "-i", merged, "-i", next_v, "-filter_complex", fc, "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-c:a", "aac", tmp]
        else:
            fc = f"[0:v][1:v]xfade=transition=fade:duration=0.8:offset={offset}[v_out]"
            cmd = ["ffmpeg", "-y", "-i", merged, "-i", next_v, "-filter_complex", fc, "-map", "[v_out]", "-c:v", "libx264", tmp]
        subprocess.run(cmd, check=True)
        merged = tmp
    return merged

def main():
    prompts = {}
    facts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 2: prompts[idx] = parts[1].strip()
                if len(parts) >= 5: facts[idx] = parts[4].strip() # 5th Part: Fact

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    total_clips = len(video_files)
    processed_clips = []
    
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, total_clips, prompts.get(idx, ""), facts.get(idx, ""))
        processed_clips.append(out_path)

    final_merged = merge_with_crossfade(processed_clips)
    if final_merged:
        os.rename(final_merged, os.path.join(OUTPUT_DIR, "Final_4K_Monetizable_Short.mp4"))
        print("🎉 4K Video Processed Successfully!")

if __name__ == "__main__":
    main()
