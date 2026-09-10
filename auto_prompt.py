import os
import re
from deep_translator import GoogleTranslator

if not os.path.exists("story.txt"):
    print("❌ story.txt file not found! Please create it and add your story.")
    exit()

# पूरी कहानी को एक बार में पढ़ें
with open("story.txt", "r", encoding="utf-8") as f:
    full_story = f.read().replace('\n', ' ')

# कहानी को वाक्यों (sentences) में तोड़ें (। . ? ! के आधार पर)
raw_sentences = re.split(r'[।\.!\?]', full_story)

# खाली स्पेस हटाएँ और जो खाली लाइनें हों उन्हें हटा दें
clean_sentences = [s.strip() for s in raw_sentences if s.strip()]

if not clean_sentences:
    print("❌ No text found in story.txt!")
    exit()

print(f"📖 Found {len(clean_sentences)} sentences. Generating prompts...")

with open("prompts.txt", "w", encoding="utf-8") as f:
    for idx, line in enumerate(clean_sentences, 1):
        try:
            # हिंदी को इंग्लिश में ट्रांसलेट करें
            eng_trans = GoogleTranslator(source='auto', target='en').translate(line)
            
            # इमेज प्रॉम्प्ट (4K, Cinematic)
            img_prompt = f"{eng_trans}, cinematic lighting, ultra realistic, highly detailed, 4k"
            
            # वीडियो प्रॉम्प्ट
            vid_prompt = "cinematic slow motion, completely silent, highly detailed"
            
            # क्लिप के लिए लाइन सेव करें (आवाज़ के लिए '।' वापस जोड़ दें ताकि TTS सही से रुके)
            f.write(f"{idx}. {img_prompt} | {vid_prompt} | {line}।\n")
            print(f"✅ Generated Prompt {idx}: {line[:30]}...")
        except Exception as e:
            print(f"⚠️ Error on line {idx}: {e}")
            
print("🎉 Magic complete! prompts.txt has been auto-generated from your story paragraph.")
