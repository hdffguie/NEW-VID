import os
import subprocess
import re
import random
import glob

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
FACE_DIR = "face_clips"  # आपके फेस क्लिप्स का फोल्डर
BGM_DIR = "bgm"          # बैकग्राउंड म्यूजिक का फोल्डर
WATERMARK_TEXT = "YOUR CHANNEL NAME"
FONT_PATH = "NotoSansHindi.ttf"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# रैंडम कलर्स की लिस्ट (Text के लिए)
TEXT_COLORS = ['yellow', 'white', 'red', 'cyan', 'magenta', '#00FF00']
# रैंडम पोजीशन्स (एनीमेशन फील के लिए)
TEXT_Y_POSITIONS = ['(h-text_h)/2', 'h-400', 'h-600', 'h-300']

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
        return len(subprocess.check_output(cmd).decode().strip()) > 0
    except: return False

def get_random_face_clip():
    """ 100 फेस क्लिप्स में से एक रैंडम क्लिप उठाता है और रैंडम फ़िल्टर लगाता है """
    if not os.path.exists(FACE_DIR): return None
    clips = glob.glob(os.path.join(FACE_DIR, "*.mp4"))
    if not clips: return None
    
    selected_clip = random.choice(clips)
    out_face = os.path.join(OUTPUT_DIR, "processed_face.mp4")
    
    # यूट्यूब को चकमा देने के लिए रैंडम फ़िल्टर (Color Grading Trick)
    filters = [
        "eq=contrast=1.2:brightness=0.05",
        "eq=saturation=1.3:gamma=1.1",
        "colorbalance=rs=.2:gs=-.1",
        "hue=s=1.2:h=5"
    ]
    random_filter = random.choice(filters)
    
    # फेस क्लिप को 9:16 में सेट करके फ़िल्टर लगाना
    cmd = [
        "ffmpeg", "-y", "-i", selected_clip, 
        "-vf", f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,{random_filter}", 
        "-c:v", "libx264", "-c:a", "aac", out_face
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_face

def generate_tts_with_vtt(text, index):
    """ Edge-TTS से आवाज़ और वर्ड-बाय-वर्ड टाइमिंग (VTT) दोनों जनरेट करता है """
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    vtt_path = os.path.join(OUTPUT_DIR, f"audio_{index}.vtt")
    
    cmd = [
        "edge-tts", "--voice", "hi-IN-MadhurNeural", "--rate=+4%", "--pitch=-2Hz", 
        "--text", text, "--write-media", audio_path, "--write-subtitles", vtt_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path, vtt_path

def process_single_clip(input_path, output_path, index, story_text):
    audio_path, vtt_path = None, None
    if story_text:
        audio_path, vtt_path = generate_tts_with_vtt(story_text, index)
    
    # वीडियो क्रॉपिंग
    scale_filter = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840"
    
    # 🎨 रैंडम कलर और रैंडम एनीमेशन पोजीशन
    vid_color = random.choice(TEXT_COLORS)
    vid_y_pos = random.choice(TEXT_Y_POSITIONS)
    
    base_filter = f"{scale_filter},eq=contrast=1.05:saturation=1.1,fps=30"

    # 🔠 वर्ड-बाय-वर्ड सबटाइटल जनरेटर (VTT to Drawtext Converter)
    # यह VTT फाइल को पढ़कर वर्ड-बाय-वर्ड पॉप-अप टेक्स्ट बनाता है
    if vtt_path and os.path.exists(vtt_path):
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
        
        words_data = re.findall(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)\n', vtt_content)
        for start, end, word in words_data:
            # टाइम को सेकंड्स में बदलना
            h, m, s = start.split(':')
            start_sec = float(h)*3600 + float(m)*60 + float(s)
            h, m, s = end.split(':')
            end_sec = float(h)*3600 + float(m)*60 + float(s)
            
            clean_word = word.strip().replace("'", "").replace(":", "")
            if clean_word:
                # हर शब्द स्क्रीन पर रैंडम कलर के साथ पॉप होगा
                base_filter += f",drawtext=fontfile={FONT_PATH}:text='{clean_word}':fontcolor={vid_color}:box=1:boxcolor=black@0.6:boxborderw=20:fontsize=150:x=(w-text_w)/2:y={vid_y_pos}:enable='between(t,{start_sec},{end_sec})'"

    # 📌 रैंडम पॉप-अप (LIKE & SUBSCRIBE) - 2 से 4 बार वीडियो में
    num_popups = random.randint(2, 4)
    for _ in range(num_popups):
        t_start = random.uniform(1.0, 4.0)
        t_end = t_start + 1.5  # 1.5 सेकंड तक दिखेगा
        base_filter += f",drawtext=fontfile={FONT_PATH}:text='LIKE & SUBSCRIBE 👍':fontcolor=white:box=1:boxcolor=red@0.8:fontsize=90:x=(w-text_w)/2:y=h-250:enable='between(t,{t_start},{t_end})'"

    v_has_audio = has_audio_stream(input_path)

    # वीडियो और ऑडियो मर्जिंग
    if audio_path and os.path.exists(audio_path):
        v_dur = get_duration(input_path)
        a_dur = get_duration(audio_path)
        v_pts_factor = (a_dur / v_dur) if v_dur > 0 else 1
        
        fc = f"[0:v]setpts={v_pts_factor:.4f}*PTS,{base_filter}[v_out]; [1:a]volume=1.6[a_out]"
        cmd = ["ffmpeg", "-y", "-i", input_path, "-i", audio_path, "-filter_complex", fc, "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", "-c:a", "aac", output_path]
        subprocess.run(cmd, check=True)
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", base_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", output_path]
        subprocess.run(cmd, check=True)
    
    return output_path

def add_bgm_to_final(video_path):
    """ पूरी वीडियो के पीछे रैंडम बैकग्राउंड म्यूजिक ऐड करता है """
    if not os.path.exists(BGM_DIR): return video_path
    bgms = glob.glob(os.path.join(BGM_DIR, "*.mp3"))
    if not bgms: return video_path
    
    random_bgm = random.choice(bgms)
    final_output = os.path.join(OUTPUT_DIR, "Final_4K_Monetizable_Short.mp4")
    
    print(f"🎵 Adding Background Music: {random_bgm}")
    # BGM वॉल्यूम 10%, मेन ऑडियो 100%
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-stream_loop", "-1", "-i", random_bgm,
        "-filter_complex", "[0:a]volume=1.0[main]; [1:a]volume=0.10[bgm]; [main][bgm]amix=inputs=2:duration=first:dropout_transition=2[a_out]",
        "-map", "0:v", "-map", "[a_out]", "-c:v", "copy", "-c:a", "aac", final_output
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return final_output

def main():
    prompts = {}
    if os.path.exists("prompts.txt"):
        with open("prompts.txt", "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines(), 1):
                parts = line.split("|")
                if len(parts) >= 2: prompts[idx] = parts[1].strip()

    video_files = sorted([os.path.join(r, f) for r, d, files in os.walk(INPUT_DIR) for f in files if f.endswith(".mp4")], key=lambda x: natural_sort_key(os.path.basename(x)))
    
    processed_clips = []
    
    # 1. 🎬 मेन AI क्लिप्स प्रोसेस करना
    for idx, v_path in enumerate(video_files, 1):
        out_path = os.path.join(OUTPUT_DIR, f"clip_{idx}.mp4")
        process_single_clip(v_path, out_path, idx, prompts.get(idx, ""))
        
        processed_clips.append(out_path)
        
        # 2. 👤 "हुक" (पहली क्लिप) के तुरंत बाद आपकी रैंडम फेस क्लिप घुसाना!
        if idx == 1:
            face_clip = get_random_face_clip()
            if face_clip:
                print("😎 Inserting Random Human Face Clip after Hook!")
                processed_clips.append(face_clip)

    # 3. ✂️ सारी क्लिप्स को जोड़ना
    merged_video = processed_clips[0]
    for i in range(1, len(processed_clips)):
        next_v = processed_clips[i]
        tmp = os.path.join(OUTPUT_DIR, f"temp_merge_{i}.mp4")
        
        # Crossfade Transition
        fc = f"[0:v][1:v]xfade=transition=fade:duration=0.5:offset={get_duration(merged_video)-0.5}[v_out]; [0:a][1:a]acrossfade=d=0.5[a_out]"
        cmd = ["ffmpeg", "-y", "-i", merged_video, "-i", next_v, "-filter_complex", fc, "-map", "[v_out]", "-map", "[a_out]", "-c:v", "libx264", "-c:a", "aac", tmp]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            merged_video = tmp
        except:
            # अगर ऑडियो में कोई दिक्कत हो तो नॉर्मल जोड़ दें
            with open("list.txt", "w") as f:
                f.write(f"file '{merged_video}'\nfile '{next_v}'\n")
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", tmp]
            subprocess.run(cmd, check=True)
            merged_video = tmp

    # 4. 🎵 लास्ट में पूरी वीडियो पर बैकग्राउंड म्यूजिक लगाना
    final_with_bgm = add_bgm_to_final(merged_video)
    
    if os.path.exists(final_with_bgm):
        print(f"🎉 MASTERPIECE GENERATED: {final_with_bgm}")

if __name__ == "__main__":
    main()
