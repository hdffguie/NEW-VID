import os
import subprocess
import re
import random
import glob

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
FACE_DIR = "face_clips"
FONT_PATH = "NotoSansHindi.ttf"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🎨 नियॉन और डार्क कलर्स (स्क्रीनशॉट जैसा)
NEON_COLORS = ['yellow', '#00FFFF', '#39FF14', '#FF00FF', 'white']

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_random_face_clip():
    """ आपकी फेस क्लिप को रैंडम फ़िल्टर के साथ उठाता है (एकदम लास्ट में लगाने के लिए) """
    if not os.path.exists(FACE_DIR): return None
    clips = glob.glob(os.path.join(FACE_DIR, "*.mp4"))
    if not clips: return None
    
    selected_clip = random.choice(clips)
    out_face = os.path.join(OUTPUT_DIR, "processed_face.mp4")
    
    # 🎭 रैंडम कलर ग्रेडिंग (यूट्यूब को चकमा देने के लिए)
    filters = [
        "eq=contrast=1.1:brightness=0.03",
        "eq=saturation=1.4",
        "colorbalance=rs=.15:bs=-.1",
        "hue=s=1.2:h=5"
    ]
    random_filter = random.choice(filters)
    
    cmd = [
        "ffmpeg", "-y", "-i", selected_clip, 
        "-vf", f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,setsar=1,fps=30,format=yuv420p,{random_filter}", 
        "-c:v", "libx264", "-c:a", "aac", "-ar", "44100", out_face
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_face

def generate_tts_with_vtt(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    vtt_path = os.path.join(OUTPUT_DIR, f"audio_{index}.vtt")
    
    cmd = [
        "edge-tts", "--voice", "hi-IN-MadhurNeural", "--rate=+15%", "--pitch=+5Hz", 
        "--text", text, "--write-media", audio_path, "--write-subtitles", vtt_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path, vtt_path

def parse_vtt(vtt_path):
    words_data = []
    if not os.path.exists(vtt_path): return words_data
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if '-->' in lines[i]:
            times = lines[i].strip().split(' --> ')
            if len(times) == 2 and i+1 < len(lines):
                try:
                    h, m, s = times[0].split(':')
                    start_sec = float(h)*3600 + float(m)*60 + float(s)
                    h, m, s = times[1].split(':')
                    end_sec = float(h)*3600 + float(m)*60 + float(s)
                    if lines[i+1].strip():
                        words_data.append((start_sec, end_sec, lines[i+1].strip()))
                except: continue
    return words_data

def process_single_clip(input_path, output_path, index, story_text, global_vid_color):
    audio_path, vtt_path = None, None
    if story_text:
        audio_path, vtt_path = generate_tts_with_vtt(story_text, index)
    
    scale_filter = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,setsar=1,format=yuv420p,fps=30"
    base_filter = f"{scale_filter},eq=contrast=1.05:saturation=1.1"

    # रैंडम एनीमेशन पोजीशन
    vid_y_pos = random.choice(['h-450', 'h-500', 'h-600', 'h-400'])

    # 🔠 वर्ड-बाय-वर्ड सबटाइटल (स्क्रीनशॉट स्टाइल: No Box, Only Shadow & Border)
    words_data = parse_vtt(vtt_path)
    for start_sec, end_sec, word in words_data:
        clean_word = word.replace("'", "").replace(":", r"\:")
        if clean_word:
            # 🎯 FIX: box=1 हटा दिया गया है, borderw=6 और shadowx=6 लगा दिया गया है (स्क्रीनशॉट जैसा)
            base_filter += f",drawtext=fontfile={FONT_PATH}:text='{clean_word}':fontcolor={global_vid_color}:bordercolor=black@0.9:borderw=6:shadowcolor=black@0.8:shadowx=6:shadowy=6:fontsize=160:x=(w-text_w)/2:y={vid_y_pos}:enable='between(t,{start_sec},{end_sec})'"

    # 📌 रैंडम पॉप-अप (LIKE & SUBSCRIBE)
    num_popups = random.randint(1, 3)
    for _ in range(num_popups):
        t_start = random.uniform(1.0, 3.5)
        t_end = t_start + 1.2
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='LIKE & SUBSCRIBE 👍':fontcolor=white:box=1:boxcolor=red@0.8:fontsize=100:x=(w-text_w)/2:y=h-250:enable='between(t,{t_start},{t_end})'"

    if audio_path and os.path.exists(audio_path):
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", f"[0:v]{base_filter}[v_out]; [1:a]volume=1.6[a_out]", "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-ar", "44100", output_path]
        subprocess.run(cmd, check=True)
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", base_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", "-ar", "44100", output_path]
        subprocess.run(cmd, check=True)
    
    return output_path

def main():
    prompts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 2: prompts[idx] = parts[1].strip()

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    
    # 🎯 1. हर वीडियो के लिए एक रैंडम कलर चुनें (जो पूरी वीडियो में सेम रहेगा)
    GLOBAL_VID_COLOR = random.choice(NEON_COLORS)
    print(f"🎨 Selected Text Color for this Video: {GLOBAL_VID_COLOR}")

    processed_clips = []
    
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, prompts.get(idx, ""), GLOBAL_VID_COLOR)
        processed_clips.append(out_path)

    # 🎬 2. एकदम लास्ट में (Outro) आपकी फेस क्लिप घुसेगी (रैंडम फ़िल्टर के साथ)
    face_clip = get_random_face_clip()
    if face_clip:
        print("😎 Inserting Random Human Face Clip at the END!")
        processed_clips.append(face_clip)

    # ✂️ 3. वीडियो मर्ज करना (No Black Screen)
    list_path = "list.txt"
    with open(list_path, "w") as f:
        for clip in processed_clips:
            f.write(f"file '{clip}'\n")
            
    final_output = os.path.join(OUTPUT_DIR, "Final_4K_Monetizable_Short.mp4")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", final_output]
    subprocess.run(cmd, check=True)

    if os.path.exists(final_output):
        print(f"🎉 MASTERPIECE GENERATED: {final_output}")

if __name__ == "__main__":
    main()
