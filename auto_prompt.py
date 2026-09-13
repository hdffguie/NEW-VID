# ==============================================================
# ⚙️ अपनी सेटिंग्स यहाँ खुद सेव करें (MANUAL SETUP)
# ==============================================================
MY_VIDEO_DURATION = 30                 # ऑप्शन: 15, 30, 45, 60 (वीडियो कितने सेकंड की बनानी है)
MY_VISUAL_STYLE = "Dark Cinematic Horror, highly detailed, realistic, creepy atmosphere"
MY_STORY_GENRE = "Horror and Scary"
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
    
    # 🚨 जादू यहाँ है: AI को First-Person (मैं, मेरा) और देहाती/लोकल स्टाइल में बोलने का कमांड दिया है
    master_prompt = f"""You are a young local guy from an Indian village telling a creepy personal experience to your friends.
    Your goal is 100% Audience Retention through intense, relatable storytelling.
    
    Task: Write a Hindi short story based on: "{topic}".
    
    CRITICAL RULES:
    1. FIRST-PERSON POV (CRITICAL): The story MUST be told in the first-person using "मैं", "मेरा", "मुझे". NEVER use third-person like "उसने", "वह".
    2. DESI/RUSTIC TONE: Use casual, local conversational Hindi (e.g., "भाई मेरी तो फट गई", "मैं चुपचाप जा रहा था", "अचानक से").
    3. VISUAL STYLE: The Image prompt MUST exactly follow this art style: {MY_VISUAL_STYLE}.
    4. CHARACTER CONSISTENCY: Describe yourself (the main character) in every prompt (e.g., a 20yo Indian boy wearing a checked shirt).
    5. EXACT LENGTH: Generate EXACTLY {target_scenes} lines.
    6. DUPLICATE TEXT: Part 1 and Part 2 must be the EXACT SAME short Hindi sentence (Max 8-12 words).
    7. FORMAT: Exactly 4 parts separated by pipe (|).
    
    8. 🎥 VIDEO PROMPT (CRITICAL LIMITATION): 
    The AI Video generator CANNOT make characters walk, run, or fight. The character MUST be stationary.
    Focus ONLY on facial expressions (shocked, crying), environmental motion (rain, wind, fog moving), and camera motion.
    ADD THIS EXACTLY AT THE END OF VIDEO PROMPT: ", no voice, no background music, high quality, 8k".
    
    Example of Good Tone: 
    रात के 2 बजे थे और मैं सुनसान सड़क से जा रहा था। | रात के 2 बजे थे और मैं सुनसान सड़क से जा रहा था। | ... | ...
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    models = ['gemini-3.6-flash', 'gemini-3.5-flash']
    
    for attempt in range(1, 6):
        print(f"\n🔄 [Attempt {attempt}/5] AI से देहाती स्क्रिप्ट मांग रहा हूँ...")
        for model_name in models:
            try:
                response = client.models.generate_content(model=model_name, contents=master_prompt)
                text = getattr(response, "text", None)
                if not text: continue

                output = text.replace("```text", "").replace("```", "").strip()
                valid_lines = [line.strip() for line in output.split('\n') if '|' in line]

                if len(valid_lines) > 0:
                    print(f"✅ SUCCESS! {model_name} ने धमाकेदार स्क्रिप्ट दे दी।")
                    return "\n".join(valid_lines[:target_scenes])
            except Exception as e:
                time.sleep(3)
                continue
    return None

def generate_ai_metadata(topic):
    print("🚀 AI से Viral SEO (Title, Tags) बनवा रहा हूँ...")
    prompt = f"""You are an expert YouTube SEO manager.
    I am making a YouTube Shorts video about this topic: "{topic}".
    Give me a viral metadata package in EXACTLY this format:
    TITLE: [A clickbait Hindi title with emojis and #shorts]
    DESC: [A short engaging description asking viewers to subscribe, with 3-4 hashtags]
    TAGS: [10 comma separated tags related to the topic]
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        text = getattr(response, "text", "")
        title_match = re.search(r"TITLE:\s*(.*)", text)
        desc_match = re.search(r"DESC:\s*([\s\S]*?)TAGS:", text)
        tags_match = re.search(r"TAGS:\s*(.*)", text)
        title = title_match.group(1).strip() if title_match else f"{topic} 😱 #shorts"
        desc = desc_match.group(1).strip() if desc_match else f"🔥 {topic}\n\nLIKE & SUBSCRIBE!"
        tags = tags_match.group(1).strip() if tags_match else "shorts, viral, trending"
        return title, desc, tags
    except Exception as e:
        return f"{topic} 😱 #shorts", f"🔥 {topic} - Watch till end!", "shorts, viral, ai"

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
