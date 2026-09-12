import os
import re
import base64
import json
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_B64 = os.getenv("YOUTUBE_TOKEN_BASE64", "")
VIDEO_FILE = "final_output/Final_4K_Monetizable_Short.mp4"
METADATA_FILE = "metadata.txt"  # 🚨 FIX: फाइल का सही रास्ता यहाँ ठीक कर दिया गया है!

def parse_metadata():
    title = "Viral Story 😱 #shorts"
    description = "Watch till the end!"
    tags = ["shorts", "viral", "trending"]
    
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            text = f.read()
            # re.IGNORECASE लगाया है ताकि Title, TITLE, title कुछ भी हो, यह पढ़ ले
            t_match = re.search(r"Title:\s*(.*)", text, re.IGNORECASE)
            d_match = re.search(r"Description:\s*([\s\S]*?)Tags:", text, re.IGNORECASE)
            tag_match = re.search(r"Tags:\s*(.*)", text, re.IGNORECASE)
            
            if t_match: title = t_match.group(1).strip()
            if d_match: description = d_match.group(1).strip()
            if tag_match: tags = [t.strip() for t in tag_match.group(1).split(",") if t.strip()]
            
    return title, description, tags

def get_schedule_time():
    """यह फंक्शन खुद तय करेगा कि वीडियो सुबह पब्लिश करनी है या शाम को"""
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30) # भारत का समय

    # 🚨 स्मार्ट लॉजिक: अगर बॉट रात 1:00 AM से 2:59 AM के बीच कभी भी चले
    if ist_now.hour < 3:
        # तो आज सुबह 5:27 AM का शेड्यूल सेट करो
        target_ist = ist_now.replace(hour=5, minute=27, second=0, microsecond=0)
        print("🌅 Morning Schedule Detected!")
    
    # 🚨 स्मार्ट लॉजिक: अगर बॉट 3:00 AM से 4:59 AM के बीच कभी भी चले
    else:
        # तो आज शाम 8:26 PM का शेड्यूल सेट करो
        target_ist = ist_now.replace(hour=20, minute=26, second=0, microsecond=0)
        print("🌃 Evening Schedule Detected!")

    # YouTube API को टाइम UTC में चाहिए, इसलिए वापस UTC में बदला
    target_utc = target_ist - datetime.timedelta(hours=5, minutes=30)
    schedule_time = target_utc.strftime("%Y-%m-%dT%H:%M:%S.0Z")
    
    print(f"📅 Video will be scheduled on YouTube for: {target_ist.strftime('%I:%M %p')} IST")
    return schedule_time

def upload_to_youtube():
    if not TOKEN_B64:
        print("⚠️ YOUTUBE_TOKEN_BASE64 is missing in secrets. Skipping YouTube upload.")
        return

    if not os.path.exists(VIDEO_FILE):
        print("❌ Video file not found! Upload failed.")
        return

    try:
        token_json = base64.b64decode(TOKEN_B64).decode('utf-8')
        creds_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(creds_data)
        
        youtube = build('youtube', 'v3', credentials=creds)
        title, description, tags = parse_metadata()
        
        # ⏰ शेड्यूल टाइम निकालें
        schedule_time = get_schedule_time()

        body = {
            'snippet': {
                'title': title[:100],  # Title max length is 100
                'description': description,
                'tags': tags,
                'categoryId': '24' # Entertainment Category
            },
            'status': {
                'privacyStatus': 'private',      
                'publishAt': schedule_time,      
                'selfDeclaredMadeForKids': False, 
                'containsSyntheticMedia': True   
            }
        }

        media = MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True, mimetype='video/mp4')
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        print(f"🚀 Uploading & Scheduling Video to YouTube...\nTitle: {title}")
        response = request.execute()
        print(f"🎉 YouTube Upload Complete! Video Scheduled Successfully.")
        print(f"🔗 Video Link: https://youtu.be/{response.get('id')}")

    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

if __name__ == "__main__":
    upload_to_youtube()
