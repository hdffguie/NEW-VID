import PIL
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import os
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip, vfx
import moviepy.audio.fx.all as afx
import re

PROMPT_FILE = "prompts.txt"
INPUT_DIR = "all_downloaded_videos"  # Jahan GitHub actions ne saari video clips save ki hain
IMAGE_FOLDER = "bing_automated_images" # Jahan images hain agar zaroorat ho
FINAL_OUTPUT = "final_output/Full_Cinematic_Movie.mp4"

os.makedirs("final_output", exist_ok=True)

# ==========================================
CREATOR_NAME = "AapkaNaam"
CHANNEL_NAME = "@AapkaChannel"   # Apna YouTube Watermark
TOPIC_NAME = "College Romance Story" 

INTRO_HOOK_TEXT = f"Dosto, main hoon {CREATOR_NAME}. Aaj ki kahani {TOPIC_NAME} ke baare mein hai. Yeh video end tak dekhna, maza aa jayega."
# ==========================================

# 🎙️ Microsoft Edge TTS Voice Generator (Madhur Neural - Hindi)
async def generate_voiceover(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+10%", pitch="+0Hz", volume="+20%")
    await communicate.save(output_file)

# ✍️ DYNAMIC CAPTIONS GENERATOR (2-WORDS POPUP WITH YELLOW/BLACK STROKE)
def create_dynamic_captions(text, duration):
    if not text: return []
    words = text.split()
    chunks = [' '.join(words[i:i+2]) for i in range(0, len(words), 2)]
    if not chunks: return []
    
    time_per_chunk = duration / len(chunks)
    text_clips = []
    current_time = 0
    for chunk in chunks:
        try:
            txt_clip = TextClip(chunk, fontsize=70, color='yellow', font="Arial-Bold", stroke_color='black', stroke_width=3)
            txt_clip = txt_clip.set_position(('center', 850))
            txt_clip = txt_clip.set_start(current_time).set_duration(time_per_chunk)
            txt_clip = txt_clip.crossfadein(0.05)
            text_clips.append(txt_clip)
        except Exception as e:
            print(f"Caption error: {e}")
        current_time += time_per_chunk
        
    return text_clips

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

async def main():
    print("🎬 STARTING AI VIDEO NARRATION & AUDIO REPLACEMENT PIPELINE...")
    
    intro_audio_path = "intro_voice.mp3"
    await generate_voiceover(INTRO_HOOK_TEXT, intro_audio_path)
    
    # Prompts file se dialogues/voiceovers padhna
    scenes = []
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if line:
                    parts = line.split('|')
                    # Agar pipe '|' ke baad hindi dialogue hai toh use lo, nahi toh default
                    vo_text = parts[1].strip() if len(parts) > 1 else line
                    scenes.append({"video_num": idx + 1, "voiceover": vo_text})

    # Downloaded videos ko dhoondna
    video_files = []
    if os.path.exists(INPUT_DIR):
        for root, dirs, files in os.walk(INPUT_DIR):
            for file in files:
                if file.endswith(".mp4"):
                    video_files.append(os.path.join(root, file))

    video_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    
    if not video_files:
        print("❌ No video files found in input directory!")
        return

    final_clips = []
    
    for i, v_path in enumerate(video_files):
        v_num = i + 1
        # Corresponding voiceover text nikalna
        vo_text = ""
        for s in scenes:
            if s['video_num'] == v_num:
                vo_text = s['voiceover']
                break
        
        if not vo_text:
            vo_text = f"Scene number {v_num} ki kahani."

        audio_path = f"Voice_{v_num}.mp3"
        
        target_audio = intro_audio_path if i == 0 else audio_path
        text_to_speak = INTRO_HOOK_TEXT if i == 0 else vo_text
        
        if i > 0:
            print(f"🎙️ Generating Edge-TTS voice for Scene {v_num}...")
            await generate_voiceover(vo_text, audio_path)
            
        if not os.path.exists(target_audio):
            continue

        # Audio load karna aur duration pata karna
        audio = AudioFileClip(target_audio)
        duration = audio.duration + 0.2  # Thoda extra buffer

        print(f"🎞️ Processing Video Clip {v_num} and syncing with voice...")
        
        # 1. VIDEO CLIP KI ORIGINAL SOUND KO 0 (MUTE) KARNA
        video_clip = VideoFileClip(v_path)
        video_clip = video_clip.without_audio() # Yahan original sound 0 ho gayi!
        
        # Agar video choti hai audio se, toh use loop ya extend kar sakte hain, ya video ki speed match kar sakte hain
        # Yahan hum video ko audio ki duration ke barabar set kar rahe hain
        if video_clip.duration < duration:
            video_clip = video_clip.fx(vfx.loop, duration=duration)
        else:
            video_clip = video_clip.subclip(0, duration)

        # Video resizing (1080p) & Color grading
        video_clip = video_clip.resize(height=1080).set_position("center")
        
        # 🟢 DYNAMIC CAPTIONS ADD KARNA 🟢
        dynamic_captions = create_dynamic_captions(text_to_speak, duration)
        
        # Video ke upar captions combine karna
        scene_composite = CompositeVideoClip([video_clip] + dynamic_captions)
        scene_composite = scene_composite.set_audio(audio)
        
        if i > 0: 
            scene_composite = scene_composite.crossfadein(0.5)
            
        final_clips.append(scene_composite)

    if not final_clips:
        print("❌ No final clips generated!")
        return

    print("✂️ Assembling Final Cinematic Movie Timeline...")
    final_video = concatenate_videoclips(final_clips, method="compose", padding=-0.3)
    
    # WATERMARK ADD KARNA
    try:
        watermark = TextClip(f" {CHANNEL_NAME} ", fontsize=40, color='white', font="Arial-Bold", bg_color='black')
        watermark = watermark.set_opacity(0.5).set_position(("right", "top")).set_duration(final_video.duration)
        final_video = CompositeVideoClip([final_video, watermark])
    except Exception as e:
        print(f"Watermark skip error: {e}")

    # BACKGROUND MUSIC (BGM) MIXING (Halki awaaz mein background music)
    bg_music_path = "bg.mp3" 
    if os.path.exists(bg_music_path):
        print("🎵 Mixing Background Music...")
        bg_clip = AudioFileClip(bg_music_path).fx(afx.volumex, 0.06).fx(afx.audio_loop, duration=final_video.duration)
        final_mixed_audio = CompositeAudioClip([final_video.audio, bg_clip])
        final_video = final_video.set_audio(final_mixed_audio)

    print(f"💾 Exporting Final Masterpiece... {FINAL_OUTPUT}")
    final_video.write_videofile(FINAL_OUTPUT, fps=24, codec="libx264", audio_codec="aac", threads=4, preset="medium")
    print("✅ FULL CINEMATIC STORY VIDEO WITH MICROSOFT NARRATOR & ZERO ORIGINAL AUDIO READY!!")

if __name__ == "__main__":
    asyncio.run(main())
