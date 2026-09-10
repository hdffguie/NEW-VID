import os
import random
import re
import time
from deep_translator import GoogleTranslator

def safe_translate(text, translator):
    if not text.strip():
        return text
    for attempt in range(3):
        try:
            result = translator.translate(text)
            # अगर गूगल ट्रांसलेटर का सर्वर एरर आया है, तो उसे रिजेक्ट करें
            if result and "Error 500" not in result and "Server Error" not in result:
                return result
        except Exception:
            time.sleep(1)
    # अगर ट्रांसलेशन फ़ेल हो जाए तो ओरिजिनल टेक्स्ट ही यूज़ करेगा
    return text

def generate_prompts_and_metadata():
    if not os.path.exists("story.txt"):
        print("❌ story.txt file not found!")
        return

    with open("story.txt", "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print("❌ story.txt is empty!")
        return

    raw_sentences = re.split(r'[\n.।]+', content)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    first_clip_motion = "dramatic 360-degree slow pan, upward camera sweep"
    random_motions = [
        "slow punchy zoom in",
        "smooth slow zoom out",
        "subtle push in shot",
        "gentle horizontal tracking shot",
        "macro focus with slow forward camera drift"
    ]

    MASTER_AUDIO_PROMPT = "STRICTLY NO HUMAN VOICE, NO BACKGROUND MUSIC. Only high quality cinematic sound effects, whooshes, and environmental impacts."

    translator = GoogleTranslator(source='auto', target='en')
    prompts = []

    for idx, sentence in enumerate(sentences, 1):
        translated = safe_translate(sentence, translator)
        motion = first_clip_motion if idx == 1 else random.choice(random_motions)
        
        # 🖼️ Image Prompt (सुरक्षित 380 कैरेक्टर सीमा)
        image_prompt = f"{translated}, {motion}, ultra-realistic, cinematic lighting, 8k resolution, highly detailed"
        if len(image_prompt) > 380:
            image_prompt = image_prompt[:380]

        # 🎥 Video Prompt (मास्टर ऑडियो प्रॉम्प्ट के साथ)
        video_prompt = f"{translated}, {motion}, {MASTER_AUDIO_PROMPT}, ultra-realistic, cinematic lighting, 8k resolution"

        prompts.append(f"{idx} | {sentence} | {image_prompt} | {video_prompt}")

    with open("prompts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))
    print(f"✅ prompts.txt generated safely with {len(prompts)} prompts!")

    first_sentence = sentences[0] if sentences else "Viral Story"
    metadata_content = f"""📌 YOUTUBE SEO METADATA

🎬 Title: {first_sentence[:50]}... 😱 #Shorts #Viral

📝 Description:
{content}

---
Watch until the end for a shocking twist! Don't forget to Like & Subscribe for more amazing stories.

🏷️ Hashtags:
#Shorts #HindiStories #ViralShorts #Trending #AIStories #MoralStories #YouTubeShorts
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(metadata_content)
    print("✅ metadata.txt generated successfully!")

if __name__ == "__main__":
    generate_prompts_and_metadata()
