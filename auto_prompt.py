import os
import sys
import math
from google import genai

STORY_FILE = "story.txt"
PROMPT_FILE = "prompts.txt"
METADATA_FILE = "metadata.txt"

VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", 60))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_ai_script(topic):
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY नहीं मिली!")
        sys.exit(1)

    target_scenes = max(3, math.ceil(VIDEO_DURATION / 5))
    
    # 🎯 FIX: यहाँ AI को "Sound Effects" वाली लाइन जोड़ने को कहा गया है।
    master_prompt = f"""You are a viral Gen-Z stand-up comedian and elite meme creator.
    
    Task: Write a HILARIOUS, extremely relatable Hindi comedy short story based on: "{topic}".
    
    CRITICAL RULES (FOLLOW STRICTLY OR SYSTEM WILL CRASH):
    1. EXACT LENGTH: Generate EXACTLY {target_scenes} lines. Not 1 less, not 1 more.
    2. FORMAT: Every single line MUST have exactly 4 parts separated by the pipe (|) symbol.
    3. THE HOOK: The FIRST line MUST be a highly relatable, funny setup.
    4. HINDI AUDIO: Short Hindi sentences (10-14 words).
    5. IMAGE PROMPT: Funny 3D Pixar/Caricature style, EXAGGERATED facial expressions, colorful and bright.
    6. VIDEO PROMPT: Short motion prompt for AI video generation. YOU MUST ADD THIS EXACT TEXT AT THE END OF EVERY VIDEO PROMPT: ", no voice, no background music, only high quality sound effects".
    
    Format Example (Line by Line):
    Hindi text | Hindi text | Funny 3D Pixar Image Prompt | English Video Prompt, no voice, no background music, only high quality sound effects
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        models = ['gemini-2.0-flash', 'gemini-3.6-flash', 'gemini-1.5-flash']
        
        response = None
        for model_name in models:
            try:
                response = client.models.generate_content(model=model_name, contents=master_prompt)
                if response and response.text:
                    break
            except: pass

        if not response or not hasattr(response, 'text') or not response.text: return None
            
        output = response.text.replace("```text", "").replace("```", "").strip()
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        if len(valid_lines) == 0: return None
            
        return "\n".join(valid_lines[:target_scenes])

    except Exception as e:
        return None

def process_stories():
    if not os.path.exists(STORY_FILE): sys.exit(1)
    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content: sys.exit(1)
        
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    
    ai_output = generate_ai_script(current_topic)
    if not ai_output: sys.exit(1)
        
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(ai_output + "\n")

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"Title: {current_topic} - Comedy Shorts\nDescription: Watch till end! 😂\nTags: shorts, comedy, relatable")

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if len(topics) > 1 else "")

if __name__ == "__main__":
    process_stories()
