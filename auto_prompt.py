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
    
    # 🎥 कैमरा मोशन्स
    first_clip_motion = "dramatic 360-degree slow pan, upward camera sweep, high tension"
    random_motions = [
        "slow punchy zoom in, high focus",
        "smooth slow zoom out, revealing details",
        "subtle push in shot, cinematic 4k",
        "gentle horizontal tracking shot",
        "macro focus with slow forward camera drift"
    ]

    # 🔊 मास्टर ऑडियो प्रॉम्प्ट (यह हर प्रॉम्प्ट में जाएगा ही जाएगा)
    MASTER_AUDIO_PROMPT = "STRICTLY NO HUMAN VOICE, NO BACKGROUND MUSIC. Only high quality cinematic sound effects, whooshes, and environmental impacts."

    translator = GoogleTranslator(source='auto', target='en')
    prompts = []

    for idx, sentence in enumerate(sentences, 1):
        translated = translator.translate(sentence)
        
        # पहली क्लिप के लिए अलग मोशन, बाकी के लिए रैंडम
        motion = first_clip_motion if idx == 1 else random.choice(random_motions)
        
        # 🚀 फाइनल प्रॉम्प्ट: कहानी + कैमरा मोशन + ऑडियो नियम + 8K क्वालिटी
        final_prompt = f"{translated}, {motion}, {MASTER_AUDIO_PROMPT}, ultra-realistic, cinematic lighting, 8k resolution, highly detailed"
        
        prompts.append(f"{idx} | {sentence} | {final_prompt}")

    with open("prompts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))
    print("✅ prompts.txt सफलतापूर्वक बन गई (No Voice/Music Rule Applied)!")

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
    print("✅ metadata.txt (SEO Title/Hashtags) तैयार है!")

if __name__ == "__main__":
    generate_prompts_and_metadata()
