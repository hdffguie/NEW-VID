import os
import re
from deep_translator import GoogleTranslator

STORY_FILE = "story.txt"
PROMPT_FILE = "prompts.txt"
METADATA_FILE = "metadata.txt"

def translate_to_english(text):
    try:
        return GoogleTranslator(source='hi', target='en').translate(text)
    except Exception as e:
        print(f"Translation warning: {e}")
        return text

def process_stories():
    if not os.path.exists(STORY_FILE):
        print("❌ story.txt not found!")
        return

    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print("❌ story.txt is empty!")
        return

    # कहानियों को खाली लाइनों (Paragraphs) से अलग करें
    stories = [s.strip() for s in content.split("\n\n") if s.strip()]
    if not stories:
        # अगर \n\n नहीं मिला, तो सिंगल लाइनों से अलग करें
        stories = [s.strip() for s in content.split("\n") if s.strip()]

    # केवल पहली कहानी चुनें
    current_story = stories[0]
    remaining_stories = stories[1:]

    print(f"📖 Selected Story for processing:\n{current_story}\n")

    # कहानी को वाक्यों (Sentences) में तोड़ें (। या ? या ! या .)
    raw_sentences = re.split(r'[।?!.]', current_story)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]

    if not sentences:
        sentences = [current_story]

    prompts = []
    for idx, sentence in enumerate(sentences, 1):
        eng_translation = translate_to_english(sentence)
        
        # Bing Image Prompt
        img_prompt = f"3D Pixar animation style, {eng_translation}, cinematic lighting, vibrant color palette, highly detailed, 8k resolution --ar 9:16"
        
        # Upsampler Video Motion Prompt
        vid_prompt = f"Cinematic slow motion movement of {eng_translation}, smooth camera drift, 4k ultra hd"
        
        # Format: Voiceover Text | Subtitle Text | Image Prompt | Video Motion Prompt
        line = f"{sentence} | {sentence} | {img_prompt} | {vid_prompt}"
        prompts.append(line)

    # 1. prompts.txt में केवल चुनी गई 1 कहानी के सीन लिखें
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(prompts) + "\n")

    # 2. metadata.txt तैयार करें
    story_title = sentences[0][:50] if sentences else "Hindi Moral Story"
    metadata_content = f"Title: {story_title} #shorts #story #hindi\nDescription: {current_story}\nTags: hindi stories, moral stories, shorts, viral"
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(metadata_content)

    # 3. बची हुई कहानियों को वापस story.txt में लिखें
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        if remaining_stories:
            f.write("\n\n".join(remaining_stories) + "\n")
        else:
            f.write("")

    print(f"✅ Generated {len(prompts)} scene prompts for Current Story.")
    print(f"📝 Remaining stories saved in story.txt: {len(remaining_stories)}")

if __name__ == "__main__":
    process_stories()
