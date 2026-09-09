import os
import re
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

INPUT_DIR = "all_downloaded_videos"
FINAL_OUTPUT = "Final_Long_Educational_Video.mp4"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def main():
    video_files = []
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.startswith("Scene_") and file.endswith(".mp4"):
                video_files.append(os.path.join(root, file))

    if not video_files: return
    video_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    clips = [VideoFileClip(v) for v in video_files]
    final_video = concatenate_videoclips(clips, method="compose")

    if os.path.exists("bg.mp3"):
        try:
            bg = AudioFileClip("bg.mp3").volumex(0.08).audio_loop(duration=final_video.duration)
            final_video = final_video.set_audio(CompositeAudioClip([final_video.audio, bg]))
        except Exception as e: print(f"BGM Error: {e}")

    final_video.write_videofile(FINAL_OUTPUT, fps=24, codec="libx264", audio_codec="aac")
    print("✅ FINAL 9:16 STORY VIDEO READY!")

if __name__ == "__main__":
    main()
