import os
import json
import random
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
JSON_CREDENTIALS = os.getenv("GDRIVE_JSON")

def download_random_clip():
    if not FOLDER_ID or not JSON_CREDENTIALS:
        print("❌ Credentials or Folder ID missing!")
        return

    # Bot (Service Account) से Login करना
    creds_dict = json.loads(JSON_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly'])
    drive_service = build('drive', 'v3', credentials=creds)

    print("🔍 Google Drive फोल्डर में वीडियो ढूंढ रहे हैं...")
    
    # फोल्डर के अंदर की सारी वीडियो फाइल्स की लिस्ट मंगाना
    query = f"'{FOLDER_ID}' in parents and mimeType contains 'video/' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("❌ फोल्डर में कोई वीडियो नहीं मिली! क्या आपने Bot Email को Viewer एक्सेस दिया है?")
        return

    # कोई 1 रैंडम वीडियो चुनना
    selected_video = random.choice(items)
    print(f"🎯 1 वीडियो चुनी गई: {selected_video['name']}")

    # फोल्डर बनाना (जहाँ process_videos.py वीडियो ढूंढता है)
    os.makedirs("face_clips", exist_ok=True)
    file_path = os.path.join("face_clips", selected_video['name'])

    # सिर्फ उस 1 वीडियो को डाउनलोड करना
    request = drive_service.files().get_media(fileId=selected_video['id'])
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"📥 Downloading... {int(status.progress() * 100)}%")
        
    print("✅ वीडियो सफलतापूर्वक डाउनलोड हो गई!")

if __name__ == "__main__":
    download_random_clip()
