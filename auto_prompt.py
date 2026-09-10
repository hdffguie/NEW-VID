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
    print(f"🚀 Google Gemini AI कहानी सोच रहा है...\nTopic: '{topic}'")
    
    # AI के लिए अब एकदम सख्त रूल (Strict Rules)
    master_prompt = f"""You are an elite Hollywood scriptwriter.
    
    Task: Write a highly emotional Hindi short story based on: "{topic}".
    
    CRITICAL RULES (FOLLOW STRICTLY OR SYSTEM WILL CRASH):
    1. EXACT LENGTH: Generate EXACTLY {target_scenes} lines. Not 1 less, not 1 more.
    2. FORMAT: Every single line MUST have exactly 5 parts separated by the pipe (|) symbol.
    3. NO MARKDOWN: Do not use bullet points, bold text, or markdown tables. Just plain text lines.
    4. IMAGE PROMPT: Realistic cinematic photography, 8k, highly detailed. (NO 3D, NO CARTOON).
    5. FACT: 1 short Hindi fact at the end of each line.
    
    Format Example (Line by Line):
    Hindi text | Hindi text | Realistic English Image Prompt | English Video Prompt | Hindi Fact
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 12 लाइनों के लिए gemini-2.0-flash सबसे स्मार्ट है, इसलिए उसे पहले रखा है
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

        # अगर रिस्पॉन्स खाली आया है
        if not response or not hasattr(response, 'text') or not response.text: 
            print("❌ AI ने खाली जवाब दिया (Maybe blocked by safety filters).")
            return None
            
        output = response.text.replace("```text", "").replace("```", "").strip()
        
        # सिर्फ वही लाइनें निकालें जिनमें '|' हो
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        
        if len(valid_lines) == 0:
            print("❌ AI ने फॉर्मेट फॉलो नहीं किया (Pipe '|' गायब है).")
            return None
            
        return "\n".join(valid_lines[:target_scenes])

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def process_stories():
    if not os.path.exists(STORY_FILE):
        print("❌ story.txt not found!")
        sys.exit(1)
        
    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    if not content:
        print("❌ story.txt is empty!")
        sys.exit(1)
        
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    
    ai_output = generate_ai_script(current_topic)
    
    # 🎯 FIX: यहाँ क्रैश होता था! अब अगर ai_output खाली होगा, तो कोड सेफली रुक जाएगा।
    if not ai_output:
        print("❌ AI Script नहीं बन पाई। कोड सुरक्षित रूप से रोक दिया गया है। कृपया दोबारा रन करें।")
        sys.exit(1)
        
    # Prompts सेव करें
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(ai_output + "\n")

    # Metadata सेव करें
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"Title: {current_topic} - Hindi Story #shorts #story\nDescription: Watch till end!\nTags: shorts, hindi story, facts")

    # बचा हुआ टॉपिक वापस story.txt में लिखें
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(topics[1:]) + "\n" if len(topics) > 1 else "")
        
    print(f"🎉 Successfully processed topic: {current_topic}")

if __name__ == "__main__":
    process_stories()
