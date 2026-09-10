import os
import random
import re
import time
from deep_translator import GoogleTranslator

STORY_FILE = "story.txt"

def safe_translate(text, translator):
    if not text.strip(): return text
    for attempt in range(3):
        try:
            result = translator.translate(text)
            if result and "Error 500" not in result and "Server Error" not in result:
                return result
        except Exception:
            time.sleep(1)
    return text

def process_bulk_stories():
    if not os.path.exists(STORY_FILE):
        print("❌ story.txt file missing!")
        return None

    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    stories = [s.strip() for s in content.split("===STORY===") if s.strip()]

    if not stories:
        print("❌ No stories found in story.txt!")
        return None

    # पहली कहानी पिक करें
    current_story = stories[0]
    remaining_stories = stories[1:]

    # बचे हुए कहानियों को वापस story.txt में लिखें (ताकि अगली बार रिपीट न हो)
    new_content = ""
    for st in remaining_stories:
        new_content += f"===STORY===\n{st}\n"

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"📖 Processed 1 story. {len(remaining_stories)} stories remaining in queue.")
    return current_story

def generate_prompts_and_metadata():
    content = process_bulk_stories()
    if not content:
        return

    raw_sentences = re.split(r'[\n.।]+', content)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    intro_motions = [
        "dramatic 360-degree slow pan, upward camera sweep",
        "dynamic wide cinematic entrance shot, slow push in",
        "low angle epic sweep shot with soft camera movement",
        "intense slow zoom in on central subject"
    ]
    random_motions = [
        "slow punchy zoom in", "smooth slow zoom out",
        "subtle push in shot", "gentle horizontal tracking shot",
        "dramatic side pan shot"
    ]

    MASTER_AUDIO_PROMPT = "STRICTLY NO HUMAN VOICE, NO BACKGROUND MUSIC. Only high quality cinematic sound effects."
    translator = GoogleTranslator(source='auto', target='en')
    prompts = []
    selected_intro = random.choice(intro_motions)

    for idx, sentence in enumerate(sentences, 1):
        translated = safe_translate(sentence, translator)
        motion = selected_intro if idx == 1 else random.choice(random_motions)
        
        image_prompt = f"{translated}, {motion}, ultra-realistic, cinematic lighting, 8k resolution"
        if len(image_prompt) > 380: image_prompt = image_prompt[:380]

        video_prompt = f"{translated}, {motion}, {MASTER_AUDIO_PROMPT}, ultra-realistic, cinematic lighting, 8k"
        prompts.append(f"{idx} | {sentence} | {image_prompt} | {video_prompt}")

    with open("prompts.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompts))

    # Dynamic SEO Metadata
    first_sentence = sentences[0] if sentences else "Viral AI Story"
    metadata_content = f"""📌 YOUTUBE SEO METADATA

🎬 Title: {first_sentence[:55]}... 😱 #Shorts #Viral #AIStories

📝 Description:
{content}

---
Watch till the end for a shocking twist! Like & Subscribe for daily cinematic AI stories.

🏷️ Tags:
Shorts, Hindi Stories, Viral Shorts, AI Stories, Horror Stories, Trending Shorts, Moral Stories

🤖 AI_DISCLOSURE: YES
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(metadata_content)
    print("✅ prompts.txt & metadata.txt ready!")

if __name__ == "__main__":
    generate_prompts_and_metadata()
