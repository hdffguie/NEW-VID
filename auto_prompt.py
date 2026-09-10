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
    
    master_prompt = f"""You are an elite Hollywood scriptwriter.
    
    Task: Write a highly emotional Hindi short story based on: "{topic}".
    
    CRITICAL RULES:
    1. EXACT LENGTH: Generate EXACTLY {target_scenes} lines.
    2. HOOK: The FIRST line MUST be a shocking HOOK.
    3. HINDI AUDIO: Short Hindi sentences (10-14 words).
    4. IMAGE PROMPT: Write prompts for ULTRA-REALISTIC, CINEMATIC PHOTOGRAPHY. Must look like real-life National Geographic or Hollywood movie. Shot on 85mm lens, highly detailed, photorealistic. STRICTLY NO 3D, NO CARTOON, NO PIXAR.
    5. VIDEO PROMPT: Short motion prompt for AI.
    6. FACT: Write one very short "Did you know?" fact in Hindi related to the scene (Max 6-8 words).
    
    Format (5 parts separated by |):
    Hindi Sentence | Hindi Sentence | Realistic English Image Prompt | English Video Prompt | Hindi Fact
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        models = ['gemini-3.6-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
        
        response = None
        for model_name in models:
            try:
                response = client.models.generate_content(model=model_name, contents=master_prompt)
                break
            except: pass

        if not response: return None
            
        output = response.text.replace("```text", "").replace("```", "").strip()
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        return "\n".join(valid_lines[:target_scenes])

    except Exception as e:
        return None

def process_stories():
    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    
    ai_output = generate_ai_script(topics[0])
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(ai_output + "\n")

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if topics[1:] else "")

if __name__ == "__main__":
    process_stories()
