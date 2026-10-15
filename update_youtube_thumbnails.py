"""
update_youtube_thumbnails.py
Updates thumbnails on already-uploaded YouTube videos for @longsleepystory
using the YouTube Data API v3.

Run from: long-sleepy-story directory
Requires: pip install google-api-python-client google-auth-oauthlib Pillow requests
"""

import os
import json
import time
import math
import urllib.parse
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "moltbuuk_token.json")
COMPLETED  = os.path.join(BASE_DIR, "completed_stories")
READY      = os.path.join(BASE_DIR, "ready_stories")

FONT_REGULAR = r"C:\Windows\Fonts\georgia.ttf"
FONT_BOLD    = r"C:\Windows\Fonts\georgiab.ttf"
FONT_ARIAL   = r"C:\Windows\Fonts\arialbd.ttf"

CLIENT_ID     = "624724194507-98v2cabe18ja7clccic1m4oeqs9kg5n7.apps.googleusercontent.com"
CLIENT_SECRET = "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"
TOKEN_URI     = "https://oauth2.googleapis.com/token"

# ── Taglines ───────────────────────────────────────────────────────────────────
TAGLINES = {
    "10 Things I Hate About You": "Shakespeare in a Seattle high school",
    "12 Monkeys":                 "Time loops and chaos theory",
    "12 Years a Slave":           "Survival. Dignity. Freedom.",
    "12 and Holding":             "Growing up faster than time allows",
    "12":                         "One verdict. Twelve voices.",
    "127 Hours":                  "Alone. Trapped. Unbreakable.",
    "15 Minutes":                 "Fame and infamy collide at midnight",
    "17 Again":                   "A second chance at youth",
    "187":                        "A teacher. A classroom. A crisis.",
    "2012":                       "The end of everything. The start of survival.",
    "20th Century Women":         "Three women. One boy. One summer.",
    "28 Days Later":              "The silence after the world ends",
    "30 Minutes or Less":         "A pizza delivery gone wrong",
    "42":                         "Breaking barriers on the diamond",
    "44 Inch Chest":              "Rage, love and loyalty collide",
    "48 Hrs":                     "One cop. One criminal. One night.",
    "50-50":                      "Laughter and tears through the fight",
    "500 Days of Summer":         "Boy meets girl. Girl exits story.",
    "8MM":                        "Dark secrets in the city shadows",
    "9":                          "Nine stitchpunks against the machine",
    "A Few Good Men":             "You can't handle the truth",
    "A Good Person":              "Guilt, grief and second chances",
    "A Million Miles Away":       "From farmworker to astronaut",
    "A Most Violent Year":        "An empire built one deal at a time",
    "A Prayer Before Dawn":       "Survival in a Thai prison",
    "A Quiet Place":              "Silence is the only shield",
    "A Real Pain":                "Grief shared across generations",
    "A Scanner Darkly":           "Identity dissolves in surveillance",
    "A Serious Man":              "When the universe offers no answers",
    "Above the Law":              "A cop with no limits",
    "Absolute Power":             "Witness to the unthinkable",
    "Abyss The":                  "Deep below, something wakes",
    "Ad Astra":                   "A son journeys to the edge of stars",
    "Adaptation":                 "A screenwriter spiraling beautifully",
    "Addams Family The":          "Darkly charming family nights",
    "Adjustment Bureau The":      "Fate is a door you can open",
    "Adventures of Buckaroo Banzai Across the Eighth Dimension The":
                                  "Dimension-hopping rock & roll science",
    "Affliction":                 "A man slowly losing his grip",
    "After School Special":       "Youth navigating the hard lessons",
    "AfterLife":                  "Between worlds, love lingers",
    "Agnes of God":               "Faith, mystery and a newborn's cry",
    "Air Force One":              "The president fights back at 35,000 ft",
    "Air":                        "The deal that changed basketball",
    "Airplane!":                  "A comedy flight you'll never forget",
    "Aladdin":                    "A diamond in the rough shines bright",
    "One Night in Miami":         "Four icons. One historic night.",
    "Alien 3":                    "No escape. No hope. No choice.",
    "Alien Nation":               "Two detectives. Two worlds.",
    "Alien vs Predator":          "Two hunters. One frozen battlefield.",
    "Alien":                      "In space, no one hears you breathe",
    # Old generic stories
    "The Midnight Conservatory of Glass and Starlight": "Glass, starlight and silence",
    "Echoes of the Autumn Hearth":  "Firelight and autumn lullabies",
    "The Clockmaker's Celestial Tower": "Gears turning toward dawn",
    "The Lantern Boat of Whispering Waters": "Drifting on a still river",
}

SKIP_STORIES = {"story_042", "story_043", "story_044", "story_045"}  # too-short generic ones


def get_tagline(movie_name: str) -> str:
    return TAGLINES.get(movie_name, "A cinematic journey into sleep")


def fmt_duration(minutes: float) -> str:
    hrs = minutes / 60.0
    if hrs < 1:
        return f"{int(round(minutes))} MIN"
    return f"{hrs:.1f}"


def fetch_background(movie_name: str, size=(1280, 720)) -> Image.Image:
    clean = movie_name.replace("The ", "").replace(" The", "").strip()
    prompt = (
        f"cinematic still from {clean}, dark moody atmosphere, "
        f"deep shadows, dramatic lighting, film noir, wide shot, "
        f"4k ultra hd, no text, no watermarks"
    )
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={size[0]}&height={size[1]}&nologo=true"
        f"&seed={abs(hash(movie_name)) % 99999}"
    )
    try:
        resp = requests.get(url, timeout=50)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return img.resize(size, Image.LANCZOS)
    except Exception as e:
        print(f"    ⚠  Pollinations failed ({e}), using dark fallback")
        return make_fallback_bg(size)


def make_fallback_bg(size=(1280, 720)) -> Image.Image:
    img = Image.new("RGB", size, (5, 8, 20))
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        ratio = y / h
        draw.line([(0, y), (w, y)], fill=(int(5 + 15*ratio), int(8 + 12*ratio), int(20 + 30*ratio)))
    return img


def add_text_overlay(base_img: Image.Image, movie_title: str, tagline: str, duration_label: str) -> Image.Image:
    img = base_img.copy().convert("RGBA")
    w, h = img.size

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    start_y = int(h * 0.35)
    for y in range(start_y, h):
        ratio = (y - start_y) / float(h - start_y)
        alpha = int(230 * (ratio ** 1.2))
        draw_ov.line([(0, y), (w, y)], fill=(8, 12, 22, min(240, alpha)))
    for y in range(0, int(h * 0.25)):
        ratio = 1.0 - (y / float(h * 0.25))
        alpha = int(140 * ratio)
        draw_ov.line([(0, y), (w, y)], fill=(5, 8, 16, alpha))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_eyebrow = ImageFont.truetype(FONT_REGULAR, max(22, int(h * 0.036)))
    font_sub     = ImageFont.truetype(FONT_REGULAR, max(22, int(h * 0.041)))
    font_badge   = ImageFont.truetype(FONT_ARIAL,   max(18, int(h * 0.030)))

    eyebrow = "F A L L   A S L E E P   T O"
    bbox_e = draw.textbbox((0, 0), eyebrow, font=font_eyebrow)
    ew = bbox_e[2] - bbox_e[0]
    ey = int(h * 0.66)
    draw.text(((w - ew) // 2 + 2, ey + 2), eyebrow, font=font_eyebrow, fill=(0, 0, 0))
    draw.text(((w - ew) // 2, ey),          eyebrow, font=font_eyebrow, fill=(225, 205, 155))

    title_text = movie_title.upper()
    font_t = None
    for size_step in [int(h * 0.088), int(h * 0.074), int(h * 0.060), int(h * 0.048), int(h * 0.038)]:
        font_t = ImageFont.truetype(FONT_BOLD, max(32, size_step))
        bbox_t = draw.textbbox((0, 0), title_text, font=font_t)
        if (bbox_t[2] - bbox_t[0]) < w * 0.92:
            break

    bbox_t = draw.textbbox((0, 0), title_text, font=font_t)
    tw = bbox_t[2] - bbox_t[0]
    title_y = ey + int(h * 0.048)
    draw.text(((w - tw) // 2 + 3, title_y + 3), title_text, font=font_t, fill=(0, 0, 0))
    draw.text(((w - tw) // 2, title_y),          title_text, font=font_t, fill=(255, 255, 255))

    sub_y = title_y + int(h * 0.104)
    bbox_s = draw.textbbox((0, 0), tagline, font=font_sub)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((w - sw) // 2 + 2, sub_y + 2), tagline, font=font_sub, fill=(0, 0, 0))
    draw.text(((w - sw) // 2, sub_y),          tagline, font=font_sub, fill=(200, 215, 235))

    badge_text = f"  🌙 {duration_label} HOURS  •  NO ADS  •  KOKORO NARRATION  "
    if "MIN" in duration_label:
        badge_text = f"  🌙 {duration_label}  •  NO ADS  •  KOKORO NARRATION  "
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0]
    bh_px = bbox_b[3] - bbox_b[1]
    bx = (w - bw) // 2
    by = int(h * 0.895)
    draw.rounded_rectangle(
        [bx - 14, by - 7, bx + bw + 14, by + bh_px + 9],
        radius=9, fill=(15, 22, 40), outline=(80, 105, 150), width=1,
    )
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 230, 150))

    return img


def build_credentials() -> Credentials:
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token") or token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )

    if not creds.valid or creds.expired:
        print("  🔄  Refreshing OAuth token...")
        creds.refresh(Request())
        # Save refreshed token
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

    return creds


def get_all_channel_videos(youtube) -> dict:
    """Return dict: {video_title_lower: video_id} for all channel uploads."""
    print("  📡  Fetching channel video list...")

    # Get uploads playlist ID
    ch_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_playlist = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = {}
    page_token = None
    page = 1
    while True:
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = youtube.playlistItems().list(**params).execute()
        for item in resp.get("items", []):
            title = item["snippet"]["title"].strip()
            vid_id = item["snippet"]["resourceId"]["videoId"]
            videos[title.lower()] = {"id": vid_id, "title": title}

        page_token = resp.get("nextPageToken")
        print(f"    Page {page}: {len(resp.get('items', []))} videos fetched (total so far: {len(videos)})")
        page += 1
        if not page_token:
            break
        time.sleep(0.5)

    print(f"  ✅  Total videos found: {len(videos)}")
    return videos


def load_story_metadata(base_dir: str) -> list:
    """Load metadata from completed_stories/ and ready_stories/."""
    stories = []
    for folder_name in ["completed_stories", "ready_stories"]:
        folder = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder):
            continue
        for story_id in sorted(os.listdir(folder)):
            story_path = os.path.join(folder, story_id)
            meta_path = os.path.join(story_path, "metadata.json")
            if not os.path.isfile(meta_path):
                continue
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            stories.append({
                "story_id": story_id,
                "folder": folder_name,
                "story_path": story_path,
                "original_name": meta.get("original_name", "").replace(".txt", "").strip(),
                "title": meta.get("title", ""),
                "duration_min": float(meta.get("estimated_duration_minutes", 180)),
            })
    return stories


def generate_thumb_to_temp(story: dict) -> str | None:
    """Generate thumbnail image to a temp file, return path."""
    movie_name = story["original_name"]
    if not movie_name:
        return None

    tagline    = get_tagline(movie_name)
    dur_label  = fmt_duration(story["duration_min"])

    bg     = fetch_background(movie_name)
    result = add_text_overlay(bg, movie_name, tagline, dur_label)

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    result.save(tmp.name, "JPEG", quality=95)
    tmp.close()
    return tmp.name


def upload_thumbnail(youtube, video_id: str, thumb_path: str) -> bool:
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg"),
        ).execute()
        return True
    except Exception as e:
        print(f"    ❌  thumbnails.set failed: {e}")
        return False


def main():
    print("=" * 65)
    print("  YouTube Thumbnail Updater — @longsleepystory")
    print("=" * 65)

    # Build YouTube API client
    creds   = build_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    # Fetch all channel videos (title → video_id)
    channel_videos = get_all_channel_videos(youtube)

    # Load all story metadata
    stories = load_story_metadata(BASE_DIR)
    print(f"\n  📂  Stories found: {len(stories)}")

    success = 0
    skipped = 0
    errors  = 0

    for story in stories:
        sid  = story["story_id"]
        name = story["original_name"]

        if sid in SKIP_STORIES:
            print(f"\n  ⏭   {sid}: skipping generic non-movie story")
            skipped += 1
            continue

        if not name:
            print(f"\n  ⚠   {sid}: no original_name — skipping")
            skipped += 1
            continue

        # Try to find the YouTube video by title match
        # Title format used by uploader: "{story_title} - Relaxing Cinematic Sleep Story"
        story_title = story["title"]
        expected_yt_title = f"{story_title} - Relaxing Cinematic Sleep Story"
        match_key = expected_yt_title.lower()

        video_info = channel_videos.get(match_key)
        if not video_info:
            # Fuzzy: try just the story title part
            for k, v in channel_videos.items():
                if story_title.lower() in k:
                    video_info = v
                    break

        if not video_info:
            print(f"\n  ⚠   {sid} ({name}): no YouTube video match for '{expected_yt_title}'")
            skipped += 1
            continue

        video_id = video_info["id"]
        print(f"\n  🎬  {sid}: {name}")
        print(f"       Video ID: {video_id}")

        # Check if there's already a thumbnail file; if not, generate one
        thumb_path = os.path.join(story["story_path"], "thumbnail.jpg")
        use_temp = False
        if not os.path.exists(thumb_path):
            print(f"       No local thumbnail — generating...")
            thumb_path = generate_thumb_to_temp(story)
            use_temp = True
            if not thumb_path:
                print(f"       ❌  Generation failed")
                errors += 1
                continue
        else:
            # Always regenerate for the branded design
            print(f"       Regenerating branded thumbnail...")
            thumb_path = generate_thumb_to_temp(story)
            use_temp = True

        # Upload to YouTube
        print(f"       Uploading to YouTube...")
        ok = upload_thumbnail(youtube, video_id, thumb_path)
        if ok:
            print(f"       ✅  Updated!")
            success += 1
        else:
            errors += 1

        if use_temp and os.path.exists(thumb_path):
            os.unlink(thumb_path)

        # Rate limit: YouTube API quota — be gentle
        time.sleep(2)

    print()
    print("=" * 65)
    print(f"  Done: {success} updated | {skipped} skipped | {errors} errors")
    print("=" * 65)


if __name__ == "__main__":
    main()
