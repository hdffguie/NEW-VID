import os
import re
from deep_translator import GoogleTranslator

if not os.path.exists("story.txt"):
    print("❌ story.txt file not found!")
    exit()

with open("story.txt", "r", encoding="utf-8") as f:
    full_story = f.read().replace('\n', ' ')

clean_sentences = [s.strip() for s in re.split(r'[।\.!\?]', full_story) if s.strip()]

# 🎬 यह है आपका मास्टर वीडियो प्रॉम्प्ट (यह हर क्लिप में जादू करेगा)
MASTER_VIDEO_PROMPT = (
    "Dynamic cinematic camera movement, sudden fast zoom in and zoom out, "
    "360-degree pan around the subject, cinematic top-down drone view. "
    "Fast-paced action changing every 2 seconds to keep the viewer highly engaged. "
    "Include impactful cinematic sound effects (whooshes, impacts). "
    "STRICTLY MUTE all background music and human voices, only environmental sound effects. "
    "8k resolution, ultra-detailed, hyper-realistic."
)

with open("prompts.txt", "w", encoding="utf-8") as f:
    for idx, line in enumerate(clean_sentences, 1):
        try:
            eng_trans = GoogleTranslator(source='auto', target='en').translate(line)
            img_prompt = f"{eng_trans}, cinematic lighting, ultra realistic, highly detailed, 4k"
            vid_prompt = f"{eng_trans}. {MASTER_VIDEO_PROMPT}"
            
            f.write(f"{idx}. {img_prompt} | {vid_prompt} | {line}।\n")
            print(f"✅ Generated Master Prompt {idx}")
        except Exception as e:
            print(f"⚠️ Error on line {idx}: {e}")
