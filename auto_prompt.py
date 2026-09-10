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
    
    print(f"⏱️ Video Duration: {VIDEO_DURATION} Seconds")
    print(f"🎬 Target Scenes: {target_scenes} Scenes (5 sec each)")
    print(f"🚀 Google Gemini AI कहानी (Narrator Style) सोच रहा है...\nTopic: '{topic}'")
    
    # 🎯 FIX: AI को Narrator बनाया गया है और Numbers/Timestamps लिखने से सख्त मना किया गया है।
    master_prompt = f"""You are an elite Professional Hindi Storyteller and Narrator.
    
    Task: Write a highly engaging, emotional, and realistic Hindi short story based on: "{topic}".
    
    CRITICAL RULES (FOLLOW STRICTLY OR SYSTEM WILL CRASH):
    1. EXACT LENGTH: Generate EXACTLY {target_scenes} lines. Not 1 less, not 1 more.
    2. VERY IMPORTANT (TIMING): Each Hindi sentence MUST be VERY SHORT (Maximum 8 to 12 words only). It must be speakable within 5 seconds.
    3. DUPLICATE TEXT: Part 1 and Part 2 must be the EXACT SAME Hindi sentence (Copy paste it).
    4. FORMAT: Every single line MUST have exactly 4 parts separated by the pipe (|) symbol.
    5. NARRATOR TONE: Tell a story like a serious narrator. No memes, no Gen-Z slang.
    6. PURE TEXT ONLY: DO NOT write timestamps (00:00), numbers, or English words in the Hindi text.
    7. IMAGE PROMPT: Hyper-realistic cinematic photography, real humans, 8k. STRICTLY NO 3D, NO CARTOON.
    8. VIDEO PROMPT: Short motion prompt. ADD THIS AT THE END: ", no voice, no background music, only high quality sound effects".
    
    Format Example (Line by Line):
    किसान ने लालच में सब कुछ दांव पर लगा दिया। | किसान ने लालच में सब कुछ दांव पर लगा दिया। | Realistic portrait of an old Indian farmer looking at gold coins, cinematic lighting, 8k | Slow pan shot, no voice, no background music, only high quality sound effects
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        models = ['gemini-2.0-flash', 'gemini-3.6-flash', 'gemini-1.5-flash']
        
        response = None
        for model_name in models:
            try:
                print(f"🔍 Trying Model: {model_name}...")
                response = client.models.generate_content(model=model_name, contents=master_prompt)
                if response and response.text:
                    print(f"✅ Success with {model_name}")
                    break
            except Exception as e: 
                print(f"⚠️ {model_name} failed: {e}")

        if not response or not hasattr(response, 'text') or not response.text: 
            print("❌ AI ने खाली जवाब दिया।")
            return None
            
        output = response.text.replace("```text", "").replace("```", "").strip()
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        
        if len(valid_lines) == 0:
            print("❌ AI ने फॉर्मेट फॉलो नहीं किया।")
            return None
            
        return "\n".join(valid_lines[:target_scenes])

    except Exception as e:
        print(f"❌ Error: {e}")
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
        f.write(f"Title: {current_topic} - True Story #shorts #story\nDescription: Watch till the end to know the truth!\nTags: shorts, true story, realistic, emotional")

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if len(topics) > 1 else "")
        
    print(f"🎉 Successfully processed topic: {current_topic}")

if __name__ == "__main__":
    process_stories()
