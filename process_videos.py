import os
import subprocess
import re

INPUT_DIR = "all_downloaded_videos"
OUTPUT_DIR = "final_output"
PROMPTS_FILE = "prompts.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def read_story_prompts():
    story_lines = {}
    if not os.path.exists(PROMPTS_FILE):
        return story_lines
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for idx, line in enumerate(lines, start=1):
        parts = line.split("|")
        if len(parts) >= 3:
            # तीसरा हिस्सा हमारी कहानी (Narration) है
            story_lines[idx] = parts[2].strip()
        else:
            story_lines[idx] = ""
    return story_lines

def generate_tts(text, index):
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{index}.mp3")
    # Microsoft TTS (hi-IN-SwaraNeural लड़की की आवाज़ है)
    # --rate=+15% से आवाज़ थोड़ी फ़ास्ट हो जाएगी ताकि 4-5 सेकंड में फिट आ जाए
    cmd = [
        "edge-tts", 
        "--voice", "hi-IN-SwaraNeural", 
        "--rate=+15%", 
        "--text", text, 
        "--write-media", audio_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return audio_path
    except Exception as e:
        print(f"⚠️ TTS Error for video {index}: {e}")
        return None

def polish_and_upscale_clip(input_path, output_path, index, story_text):
    audio_path = None
    if story_text:
        audio_path = generate_tts(story_text, index)

    if audio_path and os.path.exists(audio_path):
        # वीडियो और नई TTS ऑडियो को मिलाना (सिर्फ आवाज़, कोई टेक्स्ट नहीं)
        cmd = [
            "ffmpeg", "-y", "-i", input_path, "-i", audio_path,
            "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:1.0:5:5:0.0,fade=t=in:st=0:d=0.3,fade=t=out:st=4.7:d=0.3",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", 
            "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            output_path
        ]
    else:
        # अगर कोई ऑडियो नहीं है, तो सिर्फ वीडियो प्रोसेस करें
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:1.0:5:5:0.0,fade=t=in:st=0:d=0.3,fade=t=out:st=4.7:d=0.3",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", 
            output_path
        ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✨ Polished & Audio Added: {os.path.basename(input_path)}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error processing clip {index}: {e.stderr.decode()}")
        import shutil
        shutil.copy(input_path, output_path)

def main():
    if not os.path.exists(INPUT_DIR):
        print("❌ Input directory not found!")
        return

    story_lines = read_story_prompts()
    video_files = []
    
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith(".mp4"):
                video_files.append(os.path.join(root, file))

    if not video_files:
        print("❌ No video files found!")
        return

    video_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    polished_files = []
    print(f"Found {len(video_files)} video(s). Adding Story TTS and upscaling...")
    
    for idx, v_path in enumerate(video_files, start=1):
        out_path = os.path.join(OUTPUT_DIR, f"processed_{idx}.mp4")
        story_text = story_lines.get(idx, "")
        polish_and_upscale_clip(v_path, out_path, idx, story_text)
        polished_files.append(out_path)

    # सारी क्लिप्स को आपस में जोड़ना
    print("🎬 Merging all clips into a cinematic Full Movie...")
    concat_list_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for p_file in polished_files:
            f.write(f"file '{os.path.basename(p_file)}'\n")

    full_movie_path = os.path.join(OUTPUT_DIR, "Full_Cinematic_Story.mp4")
    merge_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", full_movie_path
    ]
    
    try:
        subprocess.run(merge_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Full Cinematic Story Movie successfully created with Voiceover!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Merge error: {e.stderr.decode()}")

if __name__ == "__main__":
    main()
