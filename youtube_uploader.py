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

def create_short_visual_frame(thumb_path, title, output_frame_path):
    import os
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    os.makedirs(os.path.dirname(os.path.abspath(output_frame_path)), exist_ok=True)
    canvas_w, canvas_h = 1080, 1920
    
    thumb = Image.open(thumb_path).convert('RGB')
    
    # Scale background to cover
    bg_ratio = max(canvas_w / thumb.width, canvas_h / thumb.height)
    bg_w = int(thumb.width * bg_ratio)
    bg_h = int(thumb.height * bg_ratio)
    bg = thumb.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
    
    # Crop to exact 1080x1920
    left = (bg_w - canvas_w) // 2
    top = (bg_h - canvas_h) // 2
    bg = bg.crop((left, top, left + canvas_w, top + canvas_h))
    
    # Apply heavy blur and dark overlay for bedtime aesthetics
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    dark_overlay = Image.new('RGBA', (canvas_w, canvas_h), (10, 15, 30, 170))
    bg = Image.alpha_composite(bg.convert('RGBA'), dark_overlay)
    
    # Sharp foreground artwork
    fg_w = 980
    fg_h = int(thumb.height * (fg_w / thumb.width))
    fg = thumb.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
    
    fg_x = (canvas_w - fg_w) // 2
    fg_y = (canvas_h - fg_h) // 2 - 40
    
    # Draw dark shadow behind foreground
    shadow = Image.new('RGBA', (fg_w + 20, fg_h + 20), (0, 0, 0, 190))
    bg.paste(shadow, (fg_x - 10, fg_y - 10), shadow)
    bg.paste(fg, (fg_x, fg_y))
    
    # Text and branding overlay
    draw = ImageDraw.Draw(bg)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 52)
        font_sub = ImageFont.truetype("arial.ttf", 36)
        font_badge = ImageFont.truetype("arialbd.ttf", 40)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        
    # Top Badge
    badge_text = "~ TONIGHT'S SLEEP STORY ~"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    b_w = badge_bbox[2] - badge_bbox[0]
    draw.text(((canvas_w - b_w) // 2, fg_y - 140), badge_text, fill=(255, 230, 150), font=font_badge)
    
    # Story Title above artwork
    title_display = title if len(title) <= 38 else title[:35] + "..."
    t_bbox = draw.textbbox((0, 0), title_display, font=font_large)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text(((canvas_w - t_w) // 2, fg_y - 70), title_display, fill=(255, 255, 255), font=font_large)
    
    # Bottom Call to Action
    cta_text = "Full 5-Hour Sleep Story Linked Below"
    c_bbox = draw.textbbox((0, 0), cta_text, font=font_sub)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((canvas_w - c_w) // 2, fg_y + fg_h + 80), cta_text, fill=(200, 220, 255), font=font_sub)
    
    cta_sub = "Drift into deep, peaceful sleep..."
    s_bbox = draw.textbbox((0, 0), cta_sub, font=font_sub)
    s_w = s_bbox[2] - s_bbox[0]
    draw.text(((canvas_w - s_w) // 2, fg_y + fg_h + 140), cta_sub, fill=(160, 180, 210), font=font_sub)
    
    bg.convert('RGB').save(output_frame_path, quality=95)
    return output_frame_path

def create_short_mp4(audio_file, thumbnail_path, title, output_mp4, duration=50):
    print(f"Generating 9:16 vertical Short video for '{title}' (duration: {duration}s)...")
    import os, subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
        
    temp_frame = output_mp4.replace(".mp4", "_frame.jpg")
    create_short_visual_frame(thumbnail_path, title, temp_frame)
    
    cmd = [
        ffmpeg_exe, '-y',
        '-loop', '1', '-framerate', '1',
        '-i', temp_frame,
        '-ss', '0', '-t', str(duration),
        '-i', audio_file,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest', output_mp4
    ]
    subprocess.run(cmd, check=True)
    
    try:
        if os.path.exists(temp_frame):
            os.remove(temp_frame)
    except Exception:
        pass
        
    print(f"Vertical Short rendered successfully: {output_mp4}")
    return output_mp4

def upload_short(youtube, video_file, title, long_video_id=None):
    print(f"Uploading Highlight Short {video_file} to YouTube...")
    
    desc = f"Drift into deep, peaceful sleep with tonight's atmospheric bedtime story.\n\n"
    if long_video_id:
        desc += f"🌙 Listen to the full 5-Hour Sleep Story here: https://youtu.be/{long_video_id}\n\n"
    desc += "Subscribe to @longsleepystory for nightly relaxing sleep audiobooks and soothing ambient tales.\n\n#Shorts #SleepStory #BedtimeStory #SleepAid #RelaxingMusic"
    
    body = {
        'snippet': {
            'title': f"{title} | Deep Sleep Story #Shorts",
            'description': desc,
            'tags': ['shorts', 'sleep story', 'bedtime story', 'relaxing', 'asmr', 'ambient', 'sleep aid'],
            'categoryId': '24'
        },
        'status': {
            'privacyStatus': 'public',
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
            print(f"Short Uploaded {int(status.progress() * 100)}%")
            
    short_id = response['id']
    print(f"Highlight Short uploaded successfully! ID: {short_id} (https://youtu.be/{short_id})")
    return short_id

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
    return video_id

