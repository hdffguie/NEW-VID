# ==============================================================
# ⚙️ अपनी सेटिंग्स यहाँ खुद सेव करें (सिर्फ इसे बदलना है!)
# ==============================================================
MY_VIDEO_DURATION = 30                 
MY_VISUAL_STYLE = "3D Pixar Animation style, highly expressive funny faces, vibrant colors"
MY_STORY_GENRE = "Funny, Roasting, Desi Comedy"
# ==============================================================

import os
import sys
import math
import time
import re
from google import genai

STORY_FILE = "story.txt"
PROMPT_FILE = "prompts.txt"
METADATA_FILE = "metadata.txt"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_ai_script(topic):
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY नहीं मिली!")
        sys.exit(1)

    target_scenes = max(3, math.ceil(MY_VIDEO_DURATION / 5))
    
    # 🚨 SMART AI LOGIC: अब AI कॉपी-पेस्ट नहीं करेगा, बल्कि सीन के हिसाब से खुद डायरेक्टर बनेगा!
    master_prompt = f"""You are an elite Professional YouTube Shorts Director.
    Your goal is 100% Audience Retention.
    
    Task: Write a Hindi short story based on: "{topic}".
    
    CRITICAL RULES:
    1. TONE & GENRE: The story MUST perfectly match this genre: {MY_STORY_GENRE}. 
       - If Comedy/Roast: Use first-person ("मैं", "मेरा", "मेरा दोस्त"), use funny slang.
    2. VISUAL STYLE: The Image prompt MUST exactly follow this art style: {MY_VISUAL_STYLE}.
    3. CHARACTER CONSISTENCY & CONTEXT: Describe the main character's age, clothes, and face. IF the scene involves multiple people (like 2 friends talking, or hiding behind a mother), YOU MUST DESCRIBE BOTH PEOPLE in the image prompt.
    4. EXACT LENGTH: Generate EXACTLY {target_scenes} lines.
    5. DUPLICATE TEXT: Part 1 and Part 2 must be the EXACT SAME short Hindi sentence.
    6. FORMAT: Exactly 4 parts separated by pipe (|).
    
    7. 🎥 DYNAMIC VIDEO PROMPT (CREATE CUSTOM CAMERA & SFX): 
    DO NOT COPY-PASTE EXAMPLES. You MUST INVENT unique camera movements and Sound Effects (SFX) for EACH SPECIFIC SCENE based on what is happening in the story.
    - Think like a Director: If a boy sees a lizard, write: "Fast tilt down to a tiny lizard on wall, quick pan to boy's terrified funny face, intense shaking. SFX: Cartoon scurrying, funny boing, gulp sound."
    - If 2 friends are talking: "Camera pans back and forth between the two friends, awkward stare. SFX: Cricket chirping, record scratch."
    - Always match the overall vibe of {MY_STORY_GENRE}.
    ADD THIS EXACTLY AT THE END OF VIDEO PROMPT: ", no voice, no background music, high quality, 8k".
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    models = ['gemini-3.6-flash', 'gemini-1.5-flash']
    
    for attempt in range(1, 6):
        print(f"\n🔄 [Attempt {attempt}/5] AI से {MY_STORY_GENRE} स्क्रिप्ट मांग रहा हूँ...")
        for model_name in models:
            try:
                response = client.models.generate_content(model=model_name, contents=master_prompt)
                text = getattr(response, "text", None)
                if not text: continue

                output = text.replace("```text", "").replace("```", "").strip()
                valid_lines = [line.strip() for line in output.split('\n') if '|' in line]

                if len(valid_lines) > 0:
                    print(f"✅ SUCCESS! {model_name} ने परफेक्ट स्क्रिप्ट दे दी।")
                    return "\n".join(valid_lines[:target_scenes])
            except Exception as e:
                time.sleep(3)
                continue
    return None

def generate_ai_metadata(topic):
    print("🚀 AI से Viral SEO (Title, Tags) बनवा रहा हूँ...")
    prompt = f"""You are an expert YouTube SEO manager for a channel that makes {MY_STORY_GENRE} videos.
    I am making a YouTube Shorts video about this topic: "{topic}".
    Give me a viral metadata package in EXACTLY this format:
    TITLE: [A clickbait Hindi title matching {MY_STORY_GENRE} vibe with suitable emojis and #shorts]
    DESC: [A short engaging description asking viewers to engage, with 3-4 hashtags]
    TAGS: [10 comma separated tags strictly related to {MY_STORY_GENRE}, the topic, and viral trends]
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        text = getattr(response, "text", "")
        title_match = re.search(r"TITLE:\s*(.*)", text)
        desc_match = re.search(r"DESC:\s*([\s\S]*?)TAGS:", text)
        tags_match = re.search(r"TAGS:\s*(.*)", text)
        title = title_match.group(1).strip() if title_match else f"{topic} #shorts"
        desc = desc_match.group(1).strip() if desc_match else f"🔥 {topic}\n\nLIKE & SUBSCRIBE!"
        tags = tags_match.group(1).strip() if tags_match else "shorts, viral, trending"
        return title, desc, tags
    except Exception as e:
        return f"{topic} #shorts", f"{topic}", "shorts, viral"

def process_stories():
    if not os.path.exists(STORY_FILE): sys.exit(1)
    with open(STORY_FILE, "r", encoding="utf-8") as f: content = f.read().strip()
    if not content: sys.exit(1)
        
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    
    ai_output = generate_ai_script(current_topic)
    if not ai_output: sys.exit(1)
        
    with open(PROMPT_FILE, "w", encoding="utf-8") as f: f.write(ai_output + "\n")
    title, desc, tags = generate_ai_metadata(current_topic)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nDescription: {desc}\nTags: {tags}")
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if len(topics) > 1 else "")
        
    print(f"🎉 Successfully processed topic: {current_topic}")

if __name__ == "__main__":
    process_stories()
