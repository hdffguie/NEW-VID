import os
import random
import re
from deep_translator import GoogleTranslator

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

    # 🔊 यह केवल वीडियो प्रॉम्प्ट में जाएगा
    MASTER_AUDIO_PROMPT = "STRICTLY NO HUMAN VOICE, NO BACKGROUND MUSIC. Only high quality cinematic sound effects, whooshes, and environmental impacts."

    translator = GoogleTranslator(source='auto', target='en')
    prompts = []

    for idx, sentence in enumerate(sentences, 1):
        try:
            translated = translator.translate(sentence)
        except Exception:
            translated = sentence
            
        motion = first_clip_motion if idx == 1 else random.choice(random_motions)
        
        # 🖼️ 1. Image Prompt (इमेज के लिए: ऑडियो रहित + 380 कैरेक्टर सेफ लिमिट)
        image_prompt = f"{translated}, {motion}, ultra-realistic, cinematic lighting, 8k resolution, highly detailed"
        if len(image_prompt) > 380:
            image_prompt = image_prompt[:380]

        # 🎥 2. Video Prompt (वीडियो के लिए: मास्टर ऑडियो प्रॉम्प्ट शामिल)
        video_prompt = f"{translated}, {motion}, {MASTER_AUDIO_PROMPT}, ultra-realistic, cinematic lighting, 8k resolution"

        # Format: Index | Sentence | Image_Prompt | Video_Prompt
        prompts.append(f"{idx} | {sentence} | {image_prompt} | {video_prompt}")

    with open("prompts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))
    print(f"✅ prompts.txt generated with separate Image and Video prompts!")

    # 🚀 YouTube SEO Metadata Generator
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
