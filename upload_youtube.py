import os
import re
import base64
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_B64 = os.getenv("YOUTUBE_TOKEN_BASE64", "")
VIDEO_FILE = "final_output/Final_4K_Monetizable_Short.mp4"
METADATA_FILE = "final_output/metadata.txt"

def parse_metadata():
    title = "Viral Story 😱 #shorts"
    description = "Watch till the end!"
    tags = ["shorts", "viral", "trending"]
    
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            text = f.read()
            t_match = re.search(r"Title:\s*(.*)", text)
            d_match = re.search(r"Description:\s*([\s\S]*?)Tags:", text)
            tag_match = re.search(r"Tags:\s*(.*)", text)
            
            if t_match: title = t_match.group(1).strip()
            if d_match: description = d_match.group(1).strip()
            if tag_match: tags = [t.strip() for t in tag_match.group(1).split(",") if t.strip()]
            
    return title, description, tags

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

        body = {
            'snippet': {
                'title': title[:100],  # Title max length is 100
                'description': description,
                'tags': tags,
                'categoryId': '24' # Entertainment Category
            },
            'status': {
                'privacyStatus': 'public',  # वीडियो सीधा पब्लिक होगी
                'selfDeclaredMadeForKids': False, # बच्चों के लिए नहीं है
                # 🤖 AI ALTERED CONTENT TICK (YouTube Policy)
                'containsSyntheticMedia': True 
            }
        }

        media = MediaFileUpload(VIDEO_FILE, chunksize=-1, resumable=True, mimetype='video/mp4')
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        print(f"🚀 Uploading Video to YouTube...\nTitle: {title}")
        response = request.execute()
        print(f"🎉 YouTube Upload Complete! Video Link: https://youtu.be/{response.get('id')}")

    except Exception as e:
        print(f"❌ YouTube Upload Failed: {e}")

if __name__ == "__main__":
    upload_to_youtube()
