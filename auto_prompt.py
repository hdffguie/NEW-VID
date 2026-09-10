import os
import random
from deep_translator import GoogleTranslator

def generate_prompts_and_metadata():
    if not os.path.exists("story.txt"):
        print("❌ story.txt नहीं मिली!")
        return

    with open("story.txt", "r", encoding="utf-8") as f:
        content = f.read().strip()

    sentences = [s.strip() for s in content.replace("\n", " ").split(".") if s.strip()]
    
    # 🎥 पहली क्लिप के लिए ड्रामेटिक कैमरा
    first_clip_motion = "dramatic 360-degree slow pan, upward camera sweep, high tension"
    
    # 🎥 बाकी क्लिप्स के लिए रैंडम डायनामिक मोशन्स (हर 2-3 सेकंड में व्यूअर का ध्यान रोकने के लिए)
    random_motions = [
        "slow punchy zoom in, high focus",
        "smooth slow zoom out, revealing details",
        "subtle push in shot, cinematic 4k",
        "gentle horizontal tracking shot",
        "macro focus with slow forward camera drift"
    ]

    translator = GoogleTranslator(source='auto', target='en')
    prompts = []

    for idx, sentence in enumerate(sentences, 1):
        translated = translator.translate(sentence)
        
        # पहली क्लिप को ख़ास रखें, बाकी को रैंडम
        motion = first_clip_motion if idx == 1 else random.choice(random_motions)
        
        # 4K मास्टर प्रॉम्प्ट स्ट्रक्चर
        final_prompt = f"{translated}, {motion}, ultra-realistic, cinematic lighting, 8k resolution, highly detailed"
        prompts.append(f"{idx} | {sentence} | {final_prompt}")

    with open("prompts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))
    print("✅ prompts.txt सफलतापूर्वक बन गई!")

    # 🚀 YouTube 100% SEO Metadata Generator (Title, Description, Hashtags)
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
    print("✅ metadata.txt (SEO Title/Hashtags) तैयार है!")

if __name__ == "__main__":
    generate_prompts_and_metadata()
