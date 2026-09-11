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
    1. STORY GENRE: The story MUST be exactly in this tone: {MY_STORY_GENRE}. (If Horror, make it scary. If Funny, make it a meme. If Educational, teach a lesson).
    2. VISUAL STYLE: The Image prompt MUST exactly follow this art style: {MY_VISUAL_STYLE}.
    3. CHARACTER CONSISTENCY: Describe the main character's age, clothes, and face in EVERY SINGLE IMAGE PROMPT so the face does not change across scenes.
    4. IMAGE PROMPT LIMIT: The English Image Prompt MUST BE UNDER 400 CHARACTERS. Keep it short and descriptive.
    5. EXACT LENGTH: Generate EXACTLY {target_scenes} lines.
    6. DUPLICATE TEXT: Part 1 and Part 2 must be the EXACT SAME short Hindi sentence (Max 8-12 words).
    7. FORMAT: Exactly 4 parts separated by pipe (|).
    8. VIDEO PROMPT: Short motion prompt. ADD THIS EXACTLY AT THE END: ", no voice, no background music, only high quality sound effects".
    
    Format Example:
    Short Hindi Text | Short Hindi Text | {MY_VISUAL_STYLE}, A 25yo man wearing a red shirt, [Action], highly detailed, 8k | Slow cinematic pan, no voice, no background music, only high quality sound effects
    """
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        models = ['gemini-2.0-flash', 'gemini-3.6-flash-lite', 'gemini-1.5-flash']
        
        for model_name in models:
            try:
                print(f"👉 Trying Gemini model: {model_name}")

                response = client.models.generate_content(
                    model=model_name,
                    contents=master_prompt
                )

                if not response:
                    print(f"⚠️ {model_name}: Empty response object")
                    continue

                text = getattr(response, "text", None)

                if not text:
                    print(f"⚠️ {model_name}: Empty text response")
                    print(f"Raw response: {response}")
                    continue

                output = text.replace("```text", "").replace("```", "").strip()
                valid_lines = [line.strip() for line in output.split('\n') if '|' in line]

                print(f"✅ {model_name} returned {len(valid_lines)} valid lines")

                if len(valid_lines) == 0:
                    print("⚠️ AI ने pipe format में output नहीं दिया")
                    print("AI OUTPUT:")
                    print(output)
                    continue

                return "\n".join(valid_lines[:target_scenes])

            except Exception as e:
                print(f"❌ Model {model_name} failed:")
                print(e)
                continue

        print("❌ सभी Gemini models fail हो गए")
        return None

    except Exception as e:
        print("❌ Main Gemini Error:")
        print(e)
        return None

def process_stories():
    if not os.path.exists(STORY_FILE): sys.exit(1)
    with open(STORY_FILE, "r", encoding="utf-8") as f: content = f.read().strip()
    if not content: sys.exit(1)
        
    topics = [t.strip() for t in content.split("\n") if t.strip()]
    current_topic = topics[0]
    
    ai_output = generate_ai_script(current_topic)
    if not ai_output: 
        print("❌ AI Script नहीं बन पाई।")
        sys.exit(1)
        
    with open(PROMPT_FILE, "w", encoding="utf-8") as f: f.write(ai_output + "\n")
    
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
