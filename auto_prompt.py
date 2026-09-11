# ==============================================================
# ⚙️ अपनी सेटिंग्स यहाँ खुद सेव करें (MANUAL SETUP)
# ==============================================================
MY_VIDEO_DURATION = 15                 # ऑप्शन: 15, 30, 45, 60 (वीडियो कितने सेकंड की बनानी है)
MY_VISUAL_STYLE = "2D Anime"           # ऑप्शन: "Realistic Human", "3D Pixar", "2D Anime"
MY_STORY_GENRE = "Cartoon"             # ऑप्शन: "Educational", "Funny", "Cartoon", "Sad", "Horror"
# ==============================================================

import os
import sys
import math
import time  # <-- सर्वर बिजी होने पर रुकने के लिए
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
    
    print(f"⚙️ Settings -> Duration: {MY_VIDEO_DURATION}s | Style: {MY_VISUAL_STYLE} | Genre: {MY_STORY_GENRE}")
    print(f"🚀 Google Gemini AI स्क्रिप्ट सोच रहा है...\nTopic: '{topic}'")
    
    master_prompt = f"""You are an elite Professional YouTube Scriptwriter.
    
    Task: Write a Hindi short story based on: "{topic}".
    
    CRITICAL RULES:
    1. STORY GENRE: The story MUST be exactly in this tone: {MY_STORY_GENRE}.
    2. VISUAL STYLE: The Image prompt MUST exactly follow this art style: {MY_VISUAL_STYLE}.
    3. CHARACTER CONSISTENCY: Describe the main character's age, clothes, and face in EVERY SINGLE IMAGE PROMPT so the face does not change across scenes.
    4. IMAGE PROMPT LIMIT: The English Image Prompt MUST BE UNDER 400 CHARACTERS. Keep it short and descriptive.
    5. EXACT LENGTH: Generate EXACTLY {target_scenes} lines.
    6. DUPLICATE TEXT: Part 1 and Part 2 must be the EXACT SAME short Hindi sentence (Max 8-12 words).
    7. FORMAT: Exactly 4 parts separated by pipe (|).
    8. VIDEO PROMPT: Short motion prompt. ADD THIS EXACTLY AT THE END: ", no voice, no background music, only high quality sound effects".
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    models = ['gemini-2.0-flash', 'gemini-3.5-flash-lite', 'gemini-1.5-flash']
    max_retries = 5  # 5 बार ट्राई करेगा
    
    for attempt in range(1, max_retries + 1):
        print(f"\n🔄 [Attempt {attempt}/{max_retries}] AI से स्क्रिप्ट मांग रहा हूँ...")
        
        for model_name in models:
            try:
                print(f"👉 Trying Gemini model: {model_name} ...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=master_prompt
                )

                text = getattr(response, "text", None)
                if not text:
                    continue

                output = text.replace("```text", "").replace("```", "").strip()
                valid_lines = [line.strip() for line in output.split('\n') if '|' in line]

                if len(valid_lines) > 0:
                    print(f"✅ SUCCESS! {model_name} ने स्क्रिप्ट दे दी।")
                    return "\n".join(valid_lines[:target_scenes]) # काम पूरा, आगे बढ़ो

            except Exception as e:
                print(f"❌ {model_name} फेल हो गया। Error: {e}")
                print("⏳ 5 सेकंड रुक रहा हूँ...")
                time.sleep(5)  # 5 सेकंड रुकेगा और अगले मॉडल पर जाएगा
                continue
                
        print("⚠️ इस बार सभी मॉडल फेल हो गए। 5 सेकंड बाद दोबारा पूरी कोशिश करूँगा...")
        time.sleep(5)

    print("❌ 5 बार कोशिश करने के बाद भी स्क्रिप्ट नहीं बन पाई।")
    return None

    except Exception as e:
        print("❌ Main Gemini Error:")
        print(e)
        return None

def process_stories():
    if not os.path.exists(STORY_FILE): 
        print(f"❌ {STORY_FILE} File नहीं मिली!")
        sys.exit(1)
        
    with open(STORY_FILE, "r", encoding="utf-8") as f: 
        content = f.read().strip()
        
    if not content: 
        print("❌ story.txt खाली है! कृपया कोई टॉपिक डालें।")
        sys.exit(1)
        
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    
    ai_output = generate_ai_script(current_topic)
    if not ai_output: 
        print("❌ AI Script नहीं बन पाई।")
        sys.exit(1)
        
    with open(PROMPT_FILE, "w", encoding="utf-8") as f: 
        f.write(ai_output + "\n")
    
    # 🚀 Viral SEO
    viral_title = f"{current_topic} 😱🤯 | {MY_STORY_GENRE} Story #shorts"
    viral_desc = f"🔥 {current_topic} - Watch till the end!\n\n👇 LIKE & SUBSCRIBE!\n\n#shorts #hindi #viral #{MY_STORY_GENRE.lower()} #story #ai"
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"Title: {viral_title}\nDescription: {viral_desc}\nTags: shorts, viral, {MY_STORY_GENRE.lower()}, story, ai, facts, hindi")

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if len(topics) > 1 else "")
        
    print(f"🎉 Successfully processed topic: {current_topic}")

if __name__ == "__main__":
    process_stories()
