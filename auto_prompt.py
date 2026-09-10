import os
import sys
import math
from google import genai

STORY_FILE = "story.txt"
PROMPT_FILE = "prompts.txt"
METADATA_FILE = "metadata.txt"

# GitHub Action से डेटा लेना
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", 60))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_ai_script(topic):
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY नहीं मिली! कृपया GitHub Secrets में ऐड करें।")
        sys.exit(1)

    target_scenes = max(3, math.ceil(VIDEO_DURATION / 5))
    
    print(f"⏱️ Video Duration: {VIDEO_DURATION} Seconds")
    print(f"🎬 Target Scenes: {target_scenes} Scenes (5 sec each)")
    print(f"🚀 Google Gemini AI कहानी और प्रॉम्प्ट्स सोच रहा है...\nTopic: '{topic}'")
    
    master_prompt = f"""You are an elite Hollywood scriptwriter, psychological hook expert, and Midjourney Prompt Engineer.
    
    Task: Write a highly emotional and viral Hindi short story based on the topic: "{topic}".
    
    CRITICAL RULES:
    1. EXACT LENGTH: You MUST generate EXACTLY {target_scenes} lines (scenes). No more, no less.
    2. THE HOOK (Scene 1): The VERY FIRST line MUST be a shocking, suspenseful, or deeply emotional HOOK to stop scrolling immediately.
    3. HINDI AUDIO SYNC: Every Hindi sentence must be short (MAX 10 to 14 words) so it perfectly fits a 5-second voiceover. The tone must be dramatic and emotional.
    4. IMAGE PROMPT: Write highly professional English prompts for a Pixar/Unreal Engine 5 style 3D animation. Include: subject, intense emotion, action, dramatic cinematic lighting, rich background, 8k resolution, photorealistic textures.
    5. VIDEO PROMPT: Write a short English motion prompt for AI video generation (e.g., 'Cinematic slow zoom in on crying eyes, smooth motion, emotional acting').
    
    DO NOT write any intro, outro, explanations, or scene numbers. Output STRICTLY in this exact format line by line (4 parts separated by |):
    Hindi Sentence | Hindi Sentence | English Image Prompt | English Video Prompt
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 🛡️ AUTO-FALLBACK SYSTEM: जो मॉडल काम करेगा, यह उसे खुद ढूंढ लेगा!
        available_models = [
            'gemini-1.5-flash', 
            'gemini-pro', 
            'gemini-1.0-pro', 
            'gemini-2.5-flash'
        ]
        
        response = None
        for model_name in available_models:
            try:
                print(f"🔍 Trying AI Model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=master_prompt
                )
                print(f"✅ Success! Generated script using: {model_name}")
                break  # जैसे ही सक्सेस मिलेगा, यह लूप से बाहर आ जाएगा
            except Exception as e:
                print(f"⚠️ {model_name} unavailable. Trying next...")

        if not response:
            print("❌ सभी AI मॉडल्स फेल हो गए। कृपया अपनी API Key चेक करें।")
            return None
            
        output = response.text.replace("```text", "").replace("```", "").strip()
        
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        final_lines = valid_lines[:target_scenes]
        
        if not final_lines:
            print("❌ AI ने गलत फॉर्मेट में आउटपुट दिया है।")
            return None
            
        return "\n".join(final_lines)

    except Exception as e:
        print(f"❌ Gemini AI Error: {e}")
        return None

def process_stories():
    if not os.path.exists(STORY_FILE):
        print("❌ story.txt not found!")
        sys.exit(1)

    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print("❌ story.txt is empty! Please add some topics in story.txt file.")
        sys.exit(1)

    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    remaining_topics = topics[1:]

    ai_output = generate_ai_script(current_topic)
    
    if not ai_output:
        print("⚠️ AI स्क्रिप्ट नहीं बना पाया।")
        sys.exit(1)

    print("\n✅ Gemini AI Generated Script & Prompts:\n" + ai_output + "\n")

    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(ai_output + "\n")

    metadata_content = f"Title: {current_topic} - Best Hindi Story #shorts #story\nDescription: {current_topic} - Watch till the end for a massive twist! \nTags: hindi stories, moral stories, shorts, viral, 3d animation, ai story, emotional"
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(metadata_content)

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(remaining_topics) + "\n" if remaining_topics else "")

    print(f"🎉 Successfully processed topic: {current_topic}")

if __name__ == "__main__":
    process_stories()
