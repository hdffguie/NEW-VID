import os
import subprocess
import re
import random
import glob

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
FACE_DIR = "face_clips"
BGM_DIR = "bgm"
FONT_PATH = "NotoSansHindi.ttf"

os.makedirs(OUTPUT_DIR, exist_ok=True)
NEON_COLORS = ['yellow', '#00FFFF', '#39FF14', '#FF00FF', 'white']
TEXT_Y_POSITIONS = ['h-450', 'h-500', 'h-600', 'h-400']

def natural_sort_key(s): return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        return float(subprocess.check_output(cmd).decode().strip())
    except: return 5.0

def has_audio_stream(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", file_path]
        return len(subprocess.check_output(cmd).decode().strip()) > 0
    except: return False

def get_random_face_clip():
    if not os.path.exists(FACE_DIR): return None
    clips = glob.glob(os.path.join(FACE_DIR, "*.mp4"))
    if not clips: return None
    
    selected_clip = random.choice(clips)
    out_face = os.path.join(OUTPUT_DIR, "processed_face.mp4")
    random_filter = random.choice(["eq=contrast=1.1:brightness=0.03", "eq=saturation=1.4", "hue=s=1.2:h=5"])
    
    cmd = ["ffmpeg", "-y", "-i", selected_clip, "-vf", f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,setsar=1,fps=30,format=yuv420p,{random_filter}", "-c:v", "libx264", "-b:v", "15M", "-c:a", "aac", "-b:a", "320k", out_face]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_face

def generate_tts_with_vtt(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    vtt_path = os.path.join(OUTPUT_DIR, f"audio_{index}.vtt")
    cmd = ["edge-tts", "--voice", "hi-IN-MadhurNeural", "--rate=+2%", "--pitch=+0Hz", "--text", text, "--write-media", audio_path, "--write-subtitles", vtt_path]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path, vtt_path

def parse_vtt_to_words(vtt_path):
    words_data = []
    if not os.path.exists(vtt_path): return words_data
    with open(vtt_path, 'r', encoding='utf-8') as f: content = f.read()
    blocks = re.findall(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,\.]\d{3})\n(.*?)(?=\n\n|\Z)', content, re.DOTALL)
    for start_str, end_str, text in blocks:
        text = text.replace('\n', ' ').strip()
        if not text: continue
        def to_sec(t_str):
            h, m, s = t_str.replace(',', '.').split(':')
            return float(h)*3600 + float(m)*60 + float(s)
        start_sec, end_sec = to_sec(start_str), to_sec(end_str)
        words = text.split()
        if not words: continue
        duration_per_word = (end_sec - start_sec) / len(words)
        curr_time = start_sec
        for word in words:
            words_data.append((curr_time, curr_time + duration_per_word, word.replace("'", "").replace(":", r"\:")))
            curr_time += duration_per_word
    return words_data

def process_single_clip(input_path, output_path, index, story_text, global_vid_color):
    audio_path, vtt_path = None, None
    if story_text: audio_path, vtt_path = generate_tts_with_vtt(story_text, index)
    
    scale_filter = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,setsar=1,format=yuv420p,fps=30,unsharp=5:5:1.0:5:5:0.0"
    
    stretch_filter = ""
    if audio_path and os.path.exists(audio_path):
        v_dur, a_dur = get_duration(input_path), get_duration(audio_path)
        if v_dur > 0 and a_dur > 0:
            stretch_filter = f"setpts={(a_dur/v_dur):.4f}*PTS,"

    base_filter = f"{stretch_filter}{scale_filter},eq=contrast=1.05:saturation=1.1"
    vid_y_pos = random.choice(TEXT_Y_POSITIONS)

    words_data = parse_vtt_to_words(vtt_path)
    for start_sec, end_sec, word in words_data:
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='{word}':fontcolor={global_vid_color}:bordercolor=black@0.9:borderw=8:shadowcolor=black@0.9:shadowx=8:shadowy=8:fontsize=220:x=(w-text_w)/2:y={vid_y_pos}:enable='between(t,{start_sec},{end_sec})'"

    for _ in range(random.randint(1, 3)):
        t_start = random.uniform(1.0, max(2.0, get_duration(audio_path if audio_path else input_path) - 1.5))
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='LIKE & SUBSCRIBE 👍':fontcolor=white:box=1:boxcolor=red@0.8:fontsize=100:x=(w-text_w)/2:y=h-250:enable='between(t,{t_start},{t_start+1.2})'"

    cmd_base = ["ffmpeg", "-y", "-i", input_path]
    if audio_path and os.path.exists(audio_path):
        cmd_base += ["-i", audio_path, "-filter_complex", f"[0:v]{base_filter}[v_out]; [1:a]volume=1.6[a_out]", "-map", "[v_out]", "-map", "[a_out]", "-shortest"]
    else:
        cmd_base += ["-vf", base_filter]
    
    cmd = cmd_base + ["-c:v", "libx264", "-preset", "medium", "-b:v", "15M", "-maxrate", "20M", "-bufsize", "30M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", output_path]
    subprocess.run(cmd, check=True)
    return output_path

def add_bgm_to_final(video_path):
    if not os.path.exists(BGM_DIR): return video_path
    bgms = glob.glob(os.path.join(BGM_DIR, "*.mp3"))
    if not bgms: return video_path
    
    random_bgm = random.choice(bgms)
    final_output = os.path.join(OUTPUT_DIR, "Final_4K_Monetizable_Short.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-stream_loop", "-1", "-i", random_bgm,
        "-filter_complex", "[0:a]volume=1.0[main]; [1:a]volume=0.15[bgm]; [main][bgm]amix=inputs=2:duration=first:dropout_transition=2[a_out]",
        "-map", "0:v", "-map", "[a_out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", final_output
    ]
    subprocess.run(cmd, check=True)
    return final_output

def main():
    prompts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 1: prompts[idx] = parts[0].strip()

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    GLOBAL_VID_COLOR = random.choice(NEON_COLORS)
    processed_clips = []
    
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, prompts.get(idx, ""), GLOBAL_VID_COLOR)
        processed_clips.append(out_path)

    face_clip = get_random_face_clip()
    if face_clip: processed_clips.append(face_clip)

    list_path = "list.txt"
    with open(list_path, "w") as f:
        for clip in processed_clips: f.write(f"file '{clip}'\n")
            
    merged_video = os.path.join(OUTPUT_DIR, "merged_temp.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", merged_video], check=True)
    final_with_bgm = add_bgm_to_final(merged_video)
    print(f"🎉 MASTERPIECE GENERATED: {final_with_bgm}")

if __name__ == "__main__": main()
