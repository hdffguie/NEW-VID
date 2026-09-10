import os
import requests
import urllib.parse
import math

STORY_FILE = "story.txt"
PROMPT_FILE = "prompts.txt"
METADATA_FILE = "metadata.txt"

# GitHub Action से टाइम (सेकंड्स) लेना, डिफ़ॉल्ट 60 सेकंड
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", 60))

def generate_ai_script(topic):
    # Upsampler 5 सेकंड का वीडियो बनाता है, तो लाइनें (Scenes) कैलकुलेट करें
    target_scenes = max(3, math.ceil(VIDEO_DURATION / 5))
    
    print(f"⏱️ Video Duration: {VIDEO_DURATION} Seconds")
    print(f"🎬 Target Scenes: {target_scenes} Scenes (5 sec each)")
    print(f"🤖 AI कहानी और प्रोफेशनल प्रॉम्प्ट्स सोच रहा है...\nTopic: '{topic}'")
    
    # यह है "God-Level Master Prompt" जो AI को इंस्ट्रक्शन देगा
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
    
    url = f"https://text.pollinations.ai/{urllib.parse.quote(master_prompt)}"
    
    try:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        output = response.text.strip()
        
        # फालतू का टेक्स्ट हटाने के लिए
        output = output.replace("```text", "").replace("```", "").strip()
        
        # सिर्फ वही लाइनें चुनें जिनमें "|" है
        valid_lines = [line.strip() for line in output.split('\n') if '|' in line]
        
        # AI कभी-कभी 1-2 लाइन ज्यादा दे देता है, उसे कट कर लें
        final_lines = valid_lines[:target_scenes]
        return "\n".join(final_lines)

    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")
        return None

def process_stories():
    if not os.path.exists(STORY_FILE):
        print("❌ story.txt not found!")
        return

    with open(STORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print("❌ story.txt is empty! Please add some topics.")
        return

    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    remaining_topics = topics[1:]

    ai_output = generate_ai_script(current_topic)
    
    if not ai_output:
        print("⚠️ AI स्क्रिप्ट नहीं बना पाया। कृपया कोड को दोबारा रन करें।")
        return

    print("\n✅ AI Generated Script & Prompts:\n" + ai_output + "\n")

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
