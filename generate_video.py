import PIL
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import os
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip, vfx
import moviepy.audio.fx.all as afx
import requests

PROMPT_FILE = "prompts.txt"
IMAGE_FOLDER = "ai_generated_images"
FINAL_OUTPUT = "Final_Long_Educational_Video.mp4"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

CREATOR_NAME = "Kahani Zone"
CHANNEL_NAME = "@KahaniZone"
TOPIC_NAME = "College Pyar ki Kahani"

INTRO_HOOK_TEXT = f"Dosto, dekhiye yeh khubsurat kahani. Agar aapko bhi pyaar par yakeen hai, toh video ko end tak zaroor dekhna."

async def generate_voiceover(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+15%", pitch="+2Hz", volume="+30%")
    await communicate.save(output_file)

def resize_func_zoomin(t): return 1 + 0.02 * t  
def resize_func_zoomout(t): return 1.1 - 0.02 * t 

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
            txt_clip = txt_clip.set_position(('center', 1500)) # 9:16 ke liye thoda niche position
            txt_clip = txt_clip.set_start(current_time).set_duration(time_per_chunk)
            txt_clip = txt_clip.crossfadein(0.05)
            text_clips.append(txt_clip)
        except Exception as e:
            print(f"Caption error for chunk '{chunk}': {e}")
        current_time += time_per_chunk
        
    return text_clips

def send_telegram_video(video_path, caption=""):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        if os.path.exists(video_path):
            with open(video_path, "rb") as file:
                requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"video": file}, timeout=300)
    except Exception as e:
        print(f"Telegram upload error: {e}")

async def main():
    print("🎬 STARTING 9:16 VERTICAL VIDEO PIPELINE...")
    
    intro_audio_path = "intro_voice.mp3"
    await generate_voiceover(INTRO_HOOK_TEXT, intro_audio_path)
    
    scenes = []
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if line:
                    parts = line.split('|')
                    vo_text = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                    scenes.append({"video_num": idx + 1, "voiceover": vo_text})

    final_clips = []
    
    for i, scene in enumerate(scenes):
        v_num = scene['video_num']
        vo_text = scene['voiceover']
        
        img_path = os.path.join(IMAGE_FOLDER, f"Generated_Image_{v_num}.jpg")
        audio_path = os.path.join(IMAGE_FOLDER, f"Voice_{v_num}.mp3")
        
        if not os.path.exists(img_path): 
            print(f"⚠️ Image not found: {img_path}")
            continue
            
        print(f"🎙️ Processing Scene {v_num}...")
        
        target_audio = intro_audio_path if i == 0 else audio_path
        text_to_speak = INTRO_HOOK_TEXT if i == 0 else vo_text
        
        if i > 0 and vo_text: 
            await generate_voiceover(vo_text, audio_path)
        
        if not os.path.exists(target_audio): continue

        audio = AudioFileClip(target_audio)
        duration = audio.duration + 0.3 

        # 9:16 Resolution: 1080x1920 (Vertical Reels/Shorts Format)
        img_clip = ImageClip(img_path).set_duration(duration)
        img_clip = img_clip.resize(width=1080) 
        img_clip = img_clip.fx(vfx.colorx, 1.15).fx(vfx.lum_contrast, lum=5, contrast=0.1).set_position("center")
        
        if i % 2 == 0: img_clip = img_clip.resize(resize_func_zoomin)
        else: img_clip = img_clip.resize(resize_func_zoomout)
            
        bg_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0)).set_duration(duration)
        
        # Dynamic Captions Add kar rahe hain
        dynamic_captions = create_dynamic_captions(text_to_speak, duration)
        
        video_clip = CompositeVideoClip([bg_clip, img_clip] + dynamic_captions)
        video_clip = video_clip.set_audio(audio)
        
        if i > 0: video_clip = video_clip.crossfadein(0.5)
        final_clips.append(video_clip)

    if not final_clips: 
        print("❌ No clips generated!")
        return

    print("✂️ Assembling 9:16 Vertical Timeline...")
    final_video = concatenate_videoclips(final_clips, method="compose", padding=-0.3)
    
    # Watermark
    try:
        watermark = TextClip(f" {CHANNEL_NAME} ", fontsize=40, color='white', font="Arial-Bold", bg_color='black')
        watermark = watermark.set_opacity(0.5).set_position(("center", 100)).set_duration(final_video.duration)
        final_video = CompositeVideoClip([final_video, watermark])
    except Exception as e:
        print(f"Watermark skipped: {e}")

    # Optional Background Music agar 'bg.mp3' file di ho
    bg_music_path = "bg.mp3" 
    if os.path.exists(bg_music_path):
        try:
            bg_clip = AudioFileClip(bg_music_path).fx(afx.volumex, 0.08).fx(afx.audio_loop, duration=final_video.duration)
            final_mixed_audio = CompositeAudioClip([final_video.audio, bg_clip])
            final_video = final_video.set_audio(final_mixed_audio)
        except Exception as e:
            print(f"BGM error: {e}")

    print(f"💾 Exporting 9:16 Video... {FINAL_OUTPUT}")
    final_video.write_videofile(FINAL_OUTPUT, fps=24, codec="libx264", audio_codec="aac", bitrate="5000k")
    print("✅ VERTICAL MASTERPIECE READY!")

    # Telegram par final video bhej do
    send_telegram_video(FINAL_OUTPUT, "🎬 Your 9:16 Vertical Story Video is Ready!")

if __name__ == "__main__":
    asyncio.run(main())
