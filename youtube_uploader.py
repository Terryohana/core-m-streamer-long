import os
import hashlib
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

import io

# ── Branded thumbnail constants ────────────────────────────────────────────────
_FONT_REGULAR = r"C:\Windows\Fonts\georgia.ttf"
_FONT_BOLD    = r"C:\Windows\Fonts\georgiab.ttf"
_FONT_ARIAL   = r"C:\Windows\Fonts\arialbd.ttf"
_THUMBNAIL_STYLE = os.environ.get("THUMBNAIL_STYLE", "cinematic-night-v1")

_TAGLINES = {
    "Aliens": "Colonial Marines vs. the Hive",
    "All About Eve": "Ambition wrapped in applause",
    "All About Steve": "One woman. One road trip.",
    "All of Us Strangers": "Love echoes through time and memory",
    "All the Kings Men": "Power corrupts. Ambition destroys.",
    "All the Presidents Men": "Two reporters. One conspiracy.",
    "Almost Famous": "Rock & roll never sleeps",
    "Alone in the Dark": "Darkness hides more than shadows",
    "Amadeus": "Genius and jealousy in Vienna",
    "Amelia": "Sky, courage, and open horizon",
    "American Beauty": "Look closer. Sleep deeper.",
    "American Fiction": "A writer's satire on life",
    "American Gangster": "Empire built in the shadows",
    "American Graffiti": "One last summer night cruise",
    "American History X": "Brotherhood forged through hard truth",
    "American Hustle": "Everyone hustles to survive",
    "American Madness": "A bank, a crisis, a community",
    "American Milkshake": "Small town. Big awkward summer.",
    "American Outlaws": "Riding hard on the frontier",
    "American Pie": "High school never felt so real",
    "American President The": "Love in the halls of power",
    "10 Things I Hate About You": "Shakespeare in a Seattle high school",
    "12 Monkeys": "Time loops and chaos theory",
    "12 Years a Slave": "Survival. Dignity. Freedom.",
    "127 Hours": "Alone. Trapped. Unbreakable.",
    "A Few Good Men": "You can't handle the truth",
    "A Quiet Place": "Silence is the only shield",
    "Alien": "In space, no one hears you breathe",
    "Alien 3": "No escape. No hope. No choice.",
    "Alien Nation": "Two detectives. Two worlds.",
    "Alien vs Predator": "Two hunters. One frozen battlefield.",
    "Air Force One": "The president fights back at 35,000 ft",
    "Aladdin": "A diamond in the rough shines bright",
}

def _get_tagline(movie_name, story_description=""):
    if story_description:
        first_clause = story_description.split(".", 1)[0].split(",", 1)[0].strip()
        if first_clause:
            words = first_clause.split()
            if len(words) > 7:
                first_clause = " ".join(words[:7])
            if len(first_clause) > 54:
                first_clause = first_clause[:51].rsplit(" ", 1)[0] + "…"
            return first_clause
    return _TAGLINES.get(movie_name, "A quiet world to drift through")

def _fetch_bg(movie_name, size=(1280, 720), story_description=""):
    clean = movie_name.replace("The ", "").replace(" The", "").strip()
    scene = story_description[:240].replace("\n", " ") if story_description else clean
    has_space_setting = any(word in f"{clean} {scene}".lower() for word in ("space", "alien", "planet", "starship", "galaxy"))
    atmosphere = "soft rain and reflected lamplight, " if not has_space_setting else "soft starlight and distant planetary glow, "
    setting = f"an empty rain-glossed midnight boulevard with distant amber headlights, " if any(word in f"{clean} {scene}".lower() for word in ("boulevard", "road", "drive", "car", "street")) else ""
    prompt = (
        f"wide cinematic sleep-story illustration of {setting}inspired by {scene}, {atmosphere}"
        "a clear, memorable focal point, quiet blue-hour palette with warm amber accents, "
        "calm inviting mood, empty setting, no people, no faces, no character closeups, "
        "subtle film grain, soft contrast, realistic painterly detail, "
        "clean uncluttered composition, no text, no logos, no watermarks"
    )
    encoded = urllib.parse.quote(prompt)
    seed = int(hashlib.sha256(f"{movie_name}|{scene}".encode("utf-8")).hexdigest()[:8], 16) % 99999
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={size[0]}&height={size[1]}&nologo=true"
        f"&model=flux&seed={seed}"
    )
    try:
        resp = requests.get(url, timeout=50)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return img.resize(size, Image.LANCZOS)
    except Exception:
        img = Image.new("RGB", size, (5, 8, 20))
        draw = ImageDraw.Draw(img)
        w, h = size
        for y in range(h):
            r = y / h
            draw.line([(0, y), (w, y)], fill=(int(5+15*r), int(8+12*r), int(20+30*r)))
        return img

def _apply_overlay(base_img, movie_title, tagline, duration_hrs):
    img = base_img.copy().convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    start_y = int(h * 0.40)
    for y in range(start_y, h):
        ratio = (y - start_y) / float(h - start_y)
        alpha = int(230 * (ratio ** 1.2))
        draw_ov.line([(0, y), (w, y)], fill=(8, 12, 22, min(240, alpha)))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font_eyebrow = ImageFont.truetype(_FONT_REGULAR, max(22, int(h * 0.030)))
        font_sub     = ImageFont.truetype(_FONT_REGULAR, max(22, int(h * 0.035)))
        font_badge   = ImageFont.truetype(_FONT_ARIAL,   max(18, int(h * 0.030)))
        font_t = ImageFont.truetype(_FONT_BOLD, max(48, int(h * 0.088)))
        title_text = movie_title.upper()
        for sz in [int(h*0.088), int(h*0.074), int(h*0.060), int(h*0.048)]:
            font_t = ImageFont.truetype(_FONT_BOLD, max(36, sz))
            bb = draw.textbbox((0, 0), title_text, font=font_t)
            if (bb[2] - bb[0]) < w * 0.92:
                break
    except Exception:
        font_eyebrow = font_sub = font_badge = font_t = ImageFont.load_default()
        title_text = movie_title.upper()

    eyebrow = "L O N G   S L E E P Y   S T O R Y"
    bbox_e = draw.textbbox((0, 0), eyebrow, font=font_eyebrow)
    ew = bbox_e[2] - bbox_e[0]
    ey = int(h * 0.65)
    draw.text(((w-ew)//2+2, ey+2), eyebrow, font=font_eyebrow, fill=(0, 0, 0))
    draw.text(((w-ew)//2, ey),     eyebrow, font=font_eyebrow, fill=(225, 205, 155))

    bbox_t = draw.textbbox((0, 0), title_text, font=font_t)
    tw = bbox_t[2] - bbox_t[0]
    ty = ey + int(h * 0.048)
    draw.text(((w-tw)//2+3, ty+3), title_text, font=font_t, fill=(0, 0, 0))
    draw.text(((w-tw)//2, ty),     title_text, font=font_t, fill=(255, 255, 255))

    sub_y = ty + int(h * 0.104)
    bbox_s = draw.textbbox((0, 0), tagline, font=font_sub)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((w-sw)//2+2, sub_y+2), tagline, font=font_sub, fill=(0, 0, 0))
    draw.text(((w-sw)//2, sub_y),     tagline, font=font_sub, fill=(200, 215, 235))

    badge_text = f"  {duration_hrs} HOURS  \u2022  SLEEP STORY  \u2022  KOKORO  "
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0]; bh = bbox_b[3] - bbox_b[1]
    bx = (w - bw) // 2; by = int(h * 0.895)
    draw.rounded_rectangle([bx-14, by-7, bx+bw+14, by+bh+9], radius=9,
                           fill=(15, 22, 40), outline=(80, 105, 150), width=1)
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 230, 150))
    return img

def generate_thumbnail(movie_title, duration_minutes=180, output_path=None, story_description="", art_output_path=None):
    """Generate a cinematic Long Sleepy Story thumbnail from story-specific details.
    Returns the path to the saved thumbnail file."""
    if _THUMBNAIL_STYLE != "cinematic-night-v1":
        raise ValueError(f"Unsupported THUMBNAIL_STYLE: {_THUMBNAIL_STYLE}")
    print(f"Generating {_THUMBNAIL_STYLE} thumbnail for: {movie_title}")
    if output_path is None:
        safe = movie_title.replace(" ", "_").replace("/", "_")
        output_path = f"{safe}_thumbnail.jpg"

    duration_hrs = f"{duration_minutes / 60:.1f}"
    tagline = _get_tagline(movie_title, story_description)

    bg = _fetch_bg(movie_title, story_description=story_description)
    if art_output_path:
        os.makedirs(os.path.dirname(os.path.abspath(art_output_path)), exist_ok=True)
        bg.save(art_output_path, "JPEG", quality=94)
    result = _apply_overlay(bg, movie_title, tagline, duration_hrs)
    result.save(output_path, "JPEG", quality=95)
    print(f"Thumbnail saved: {output_path}")
    return output_path

def format_youtube_title(story_title, duration_minutes):
    """Keep the story hook first and replace the repeated generic suffix."""
    hours = max(1, round(float(duration_minutes) / 60))
    suffix = f"{hours}-Hour Sleep Story"
    max_story_length = 100 - len(suffix) - 3
    story_title = " ".join(str(story_title).split())[:max_story_length].rstrip(" -|:")
    return f"{story_title} | {suffix}"

def format_short_youtube_title(story_title, duration_seconds=50):
    """Keep the story hook prominent while identifying the Short clearly."""
    seconds = max(1, round(float(duration_seconds)))
    suffix = f"| {seconds}-Second Sleep Story #Shorts"
    max_story_length = 100 - len(suffix) - 1
    story_title = " ".join(str(story_title).split())[:max_story_length].rstrip(" -|:")
    return f"{story_title} {suffix}"

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

def create_short_visual_frame(art_path, title, output_frame_path, story_description=""):
    import os
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(os.path.dirname(os.path.abspath(output_frame_path)), exist_ok=True)
    canvas_w, canvas_h = 1080, 1920

    art = Image.open(art_path).convert('RGB') if art_path and os.path.exists(art_path) else _fetch_bg(title, story_description=story_description)
    scale = max(canvas_w / art.width, canvas_h / art.height)
    resized = art.resize((int(art.width * scale), int(art.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - canvas_w) // 2
    top = (resized.height - canvas_h) // 2
    bg = resized.crop((left, top, left + canvas_w, top + canvas_h)).convert('RGBA')
    # Fade the lower third for a legible title while leaving the scene visible.
    gradient = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient)
    for y in range(int(canvas_h * .56), canvas_h):
        strength = (y - canvas_h * .56) / (canvas_h * .44)
        gd.line([(0, y), (canvas_w, y)], fill=(7, 12, 24, int(220 * strength)))
    bg = Image.alpha_composite(bg, gradient)
    draw = ImageDraw.Draw(bg)
    
    try:
        font_large = ImageFont.truetype(_FONT_BOLD, 84)
        font_sub = ImageFont.truetype(_FONT_REGULAR, 40)
        font_badge = ImageFont.truetype(_FONT_ARIAL, 36)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        
    # Small, consistent brand line
    badge_text = "L O N G   S L E E P Y   S T O R Y"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    b_w = badge_bbox[2] - badge_bbox[0]
    draw.text(((canvas_w - b_w) // 2, 190), badge_text, fill=(255, 225, 165), font=font_badge)
    
    # Story Title above artwork
    title_display = title if len(title) <= 34 else title[:31].rstrip() + "…"
    while draw.textbbox((0, 0), title_display, font=font_large)[2] > canvas_w - 100 and font_large.size > 48:
        font_large = ImageFont.truetype(_FONT_BOLD, font_large.size - 4)
    t_bbox = draw.textbbox((0, 0), title_display, font=font_large)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text(((canvas_w - t_w) // 2, 1340), title_display, fill=(255, 255, 255), font=font_large)
    
    # Bottom Call to Action
    cta_text = "THE FULL STORY IS LINKED BELOW"
    c_bbox = draw.textbbox((0, 0), cta_text, font=font_sub)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((canvas_w - c_w) // 2, 1485), cta_text, fill=(205, 220, 240), font=font_sub)
    
    bg.convert('RGB').save(output_frame_path, quality=95)
    return output_frame_path

def create_short_mp4(audio_file, thumbnail_path, title, output_mp4, duration=50, story_description=""):
    print(f"Generating 9:16 vertical Short video for '{title}' (duration: {duration}s)...")
    import os, subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = 'ffmpeg'
        
    temp_frame = output_mp4.replace(".mp4", "_frame.jpg")
    create_short_visual_frame(thumbnail_path, title, temp_frame, story_description)
    
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

def upload_short(youtube, video_file, title, long_video_id=None, thumbnail_path=None):
    print(f"Uploading Highlight Short {video_file} to YouTube...")
    
    desc = f"Drift into deep, peaceful sleep with tonight's atmospheric bedtime story.\n\n"
    if long_video_id:
        desc += f"🌙 Listen to the full 5-Hour Sleep Story here: https://youtu.be/{long_video_id}\n\n"
    desc += "Subscribe to @longsleepystory for nightly relaxing sleep audiobooks and soothing ambient tales.\n\n#Shorts #SleepStory #BedtimeStory #SleepAid #RelaxingMusic"
    
    body = {
        'snippet': {
            'title': title if title.lower().endswith("#shorts") else f"{title} #Shorts",
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
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=short_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Custom Shorts thumbnail uploaded.")
        except Exception as e:
            print(f"Custom Shorts thumbnail upload unavailable: {e}")
    print(f"Highlight Short uploaded successfully! ID: {short_id} (https://youtu.be/{short_id})")
    if long_video_id:
        print(
            "YouTube does not set the clickable Shorts 'Related video' field through the Data API. "
            "The full-story URL is in the description; select the long video in YouTube Studio to add the clickable link."
        )
        append_related_video_action_summary(long_video_id, short_id, title)
    return short_id


def append_related_video_action_summary(long_video_id, short_video_id, story_title):
    """Write the Studio follow-up into the current GitHub Actions run summary."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return False

    short_url = f"https://youtu.be/{short_video_id}"
    long_url = f"https://youtu.be/{long_video_id}"
    studio_url = f"https://studio.youtube.com/video/{short_video_id}/edit"
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write(
            f"\n### Related video follow-up: {story_title}\n\n"
            f"- Short: [{short_video_id}]({short_url})\n"
            f"- Full story: [{long_video_id}]({long_url})\n"
            f"- [Open Short in YouTube Studio]({studio_url}), choose **Related video**, select the full story above, and save.\n"
            "- This requires advanced feature access; the selected long video must be public or unlisted.\n"
        )
    return True

def upload_video(youtube, video_file, title, description, thumbnail_path):
    print(f"Uploading {video_file} to YouTube...")
    
    body = {
        'snippet': {
            'title': title,
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

