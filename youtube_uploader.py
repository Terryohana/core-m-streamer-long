import os
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

def generate_thumbnail(movie_title):
    print(f"Generating thumbnail for {movie_title}...")
    
    # Use Pollinations AI (Free, no-auth Image Generation API)
    # Create an atmospheric, sleep-story vibe prompt
    prompt = f"A beautiful, extremely soothing cinematic lofi night sky with a subtle crescent moon over dark pine trees, deep midnight blues and glowing stars, no text"
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
    
    thumbnail_path = f"{movie_title}_thumbnail.jpg"
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(thumbnail_path, 'wb') as f:
            f.write(response.content)
        print("Thumbnail downloaded successfully!")
    else:
        print("Failed to generate thumbnail via AI. Creating a solid color fallback.")
        img = Image.new('RGB', (1280, 720), color=(10, 15, 30))
        img.save(thumbnail_path)
    
    return thumbnail_path

def create_mp4(audio_file, thumbnail_path, output_mp4):
    print(f"Combining {audio_file} and {thumbnail_path} into an MP4 video...")
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
    
    # Ultra-fast FFmpeg command for static thumbnail video rendering
    cmd = [
        ffmpeg_exe, '-y',
        '-framerate', '1',
        '-loop', '1', '-i', thumbnail_path,
        '-i', audio_file,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest', output_mp4
    ]
    subprocess.run(cmd, check=True)
    print("Video rendered successfully!")
    return output_mp4

def get_authenticated_service():
    # In GitHub actions, we will load the credentials from an environment variable (GitHub Secret)
    import json
    token_json = os.environ.get("YOUTUBE_OAUTH_TOKEN")
    
    if not token_json:
        raise ValueError("YOUTUBE_OAUTH_TOKEN environment variable not set!")
        
    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)
    
    return build('youtube', 'v3', credentials=creds)

def upload_video(youtube, video_file, title, description, thumbnail_path):
    print(f"Uploading {video_file} to YouTube...")
    
    body = {
        'snippet': {
            'title': f"{title} - Relaxing Cinematic Sleep Story",
            'description': description + "\n\nWelcome to Long Sleepy Story. Drift off to atmospheric tales...",
            'tags': ['sleep story', 'relaxing', 'asmr', 'bedtime story', 'ambient'],
            'categoryId': '24' # Entertainment
        },
        'status': {
            'privacyStatus': 'public', # Or 'private'/'unlisted' for testing
            'selfDeclaredMadeForKids': False
        }
    }
    
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
    )
    
    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
            
    video_id = response['id']
    print(f"Video uploaded successfully! ID: {video_id}")
    
    # Upload Thumbnail
    print("Uploading custom thumbnail...")
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path)
    ).execute()
    print("Thumbnail uploaded successfully!")

if __name__ == '__main__':
    # Test script usage
    pass
