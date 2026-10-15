"""
regen_thumbnails.py
Regenerates all ready_stories/ thumbnails with the branded
"FALL ASLEEP TO [MOVIE NAME]" design.
Run from: long-sleepy-story directory
"""

import os
import json
import math
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
READY_DIR = os.path.join(BASE_DIR, "ready_stories")

FONT_REGULAR = r"C:\Windows\Fonts\georgia.ttf"
FONT_BOLD    = r"C:\Windows\Fonts\georgiab.ttf"
FONT_ARIAL   = r"C:\Windows\Fonts\arialbd.ttf"

# ── Taglines (movie-specific atmosphere, max ~50 chars) ────────────────────────
TAGLINES = {
    "Aliens":                     "Colonial Marines vs. the Hive",
    "All About Eve":              "Ambition wrapped in applause",
    "All About Steve":            "One woman. One reporter. One awkward road trip.",
    "All of Us Strangers":        "Love echoes through time and memory",
    "All the Kings Men":          "Power corrupts. Ambition destroys.",
    "All the Presidents Men":     "Two reporters. One conspiracy. All truth.",
    "Almost Famous":              "Rock & roll never sleeps",
    "Alone in the Dark":          "Darkness hides more than shadows",
    "Amadeus":                    "Genius and jealousy in Vienna",
    "Amelia":                     "Sky, courage, and open horizon",
    "American Beauty":            "Look closer. Sleep deeper.",
    "American Fiction":           "A writer's satire on life",
    "American Gangster":          "Empire built in the shadows",
    "American Graffiti":          "One last summer night cruise",
    "American History X":         "Brotherhood forged through hard truth",
    "American Hustle":            "Everyone hustles to survive",
    "American Madness":           "A bank, a crisis, a community",
    "American Milkshake":         "Small town. Big awkward summer.",
    "American Outlaws":           "Riding hard on the frontier",
    "American Pie":               "High school never felt so real",
    "American President The":     "Love in the halls of power",
    # Completed stories taglines
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
    # Generic fallback for old hardcoded stories
    "The Midnight Conservatory of Glass and Starlight": "Glass, starlight and silence",
    "Echoes of the Autumn Hearth":  "Firelight and autumn lullabies",
    "The Clockmaker's Celestial Tower": "Gears turning toward dawn",
    "The Lantern Boat of Whispering Waters": "Drifting on a still river",
}

def get_tagline(movie_name: str) -> str:
    """Return atmospheric tagline or sensible default."""
    return TAGLINES.get(movie_name, "A cinematic journey into sleep")


def fmt_duration(minutes: float) -> str:
    """Convert minutes to e.g. '5.9' hours string."""
    hrs = minutes / 60.0
    if hrs < 1:
        return f"{int(round(minutes))} MIN"
    return f"{hrs:.1f}"


def fetch_background(movie_name: str, size: tuple = (1280, 720)) -> Image.Image:
    """Download a movie-themed background from Pollinations AI."""
    # Clean the name for use in a prompt
    clean = movie_name.replace("The ", "").replace(" The", "").strip()
    prompt = (
        f"cinematic still from {clean}, dark moody atmosphere, "
        f"deep shadows, dramatic lighting, film noir, wide shot, "
        f"4k ultra hd, no text, no watermarks"
    )
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={size[0]}&height={size[1]}&nologo=true&seed={abs(hash(movie_name)) % 99999}"
    try:
        resp = requests.get(url, timeout=45)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return img.resize(size, Image.LANCZOS)
    except Exception as e:
        print(f"    ⚠  Background fetch failed ({e}), using dark fallback")
        return make_fallback_bg(size)


def make_fallback_bg(size: tuple = (1280, 720)) -> Image.Image:
    """Dark navy gradient fallback."""
    img = Image.new("RGB", size, (5, 8, 20))
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):
        ratio = y / h
        r = int(5 + 15 * ratio)
        g = int(8 + 12 * ratio)
        b = int(20 + 30 * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def add_text_overlay(
    base_img: Image.Image,
    movie_title: str,
    tagline: str,
    duration_label: str,
) -> Image.Image:
    """Apply the branded text overlay to a base image."""
    img = base_img.copy().convert("RGBA")
    w, h = img.size

    # ── Dark gradient overlay ──────────────────────────────────────────────────
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # Bottom darkening (where text lives)
    start_y = int(h * 0.35)
    for y in range(start_y, h):
        ratio = (y - start_y) / float(h - start_y)
        alpha = int(230 * (ratio ** 1.2))
        draw_ov.line([(0, y), (w, y)], fill=(8, 12, 22, min(240, alpha)))

    # Top vignette
    for y in range(0, int(h * 0.25)):
        ratio = 1.0 - (y / float(h * 0.25))
        alpha = int(140 * ratio)
        draw_ov.line([(0, y), (w, y)], fill=(5, 8, 16, alpha))

    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    font_eyebrow = ImageFont.truetype(FONT_REGULAR, max(22, int(h * 0.036)))
    font_title   = ImageFont.truetype(FONT_BOLD,    max(48, int(h * 0.088)))
    font_sub     = ImageFont.truetype(FONT_REGULAR, max(22, int(h * 0.041)))
    font_badge   = ImageFont.truetype(FONT_ARIAL,   max(18, int(h * 0.030)))

    # ── Eyebrow: "FALL ASLEEP TO" ─────────────────────────────────────────────
    eyebrow = "F A L L   A S L E E P   T O"
    bbox_e = draw.textbbox((0, 0), eyebrow, font=font_eyebrow)
    ew = bbox_e[2] - bbox_e[0]
    ey = int(h * 0.66)
    draw.text(((w - ew) // 2 + 2, ey + 2), eyebrow, font=font_eyebrow, fill=(0, 0, 0))
    draw.text(((w - ew) // 2, ey),          eyebrow, font=font_eyebrow, fill=(225, 205, 155))

    # ── Movie title ───────────────────────────────────────────────────────────
    title_text = movie_title.upper()
    # Scale down font if title is very long
    font_t = font_title
    for size_step in [int(h * 0.088), int(h * 0.074), int(h * 0.060), int(h * 0.048)]:
        font_t = ImageFont.truetype(FONT_BOLD, max(36, size_step))
        bbox_t = draw.textbbox((0, 0), title_text, font=font_t)
        if (bbox_t[2] - bbox_t[0]) < w * 0.92:
            break

    bbox_t = draw.textbbox((0, 0), title_text, font=font_t)
    tw = bbox_t[2] - bbox_t[0]
    title_y = ey + int(h * 0.048)
    draw.text(((w - tw) // 2 + 3, title_y + 3), title_text, font=font_t, fill=(0, 0, 0))
    draw.text(((w - tw) // 2, title_y),          title_text, font=font_t, fill=(255, 255, 255))

    # ── Tagline ───────────────────────────────────────────────────────────────
    sub_y = title_y + int(h * 0.104)
    bbox_s = draw.textbbox((0, 0), tagline, font=font_sub)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((w - sw) // 2 + 2, sub_y + 2), tagline, font=font_sub, fill=(0, 0, 0))
    draw.text(((w - sw) // 2, sub_y),          tagline, font=font_sub, fill=(200, 215, 235))

    # ── Badge ─────────────────────────────────────────────────────────────────
    # Decide whether duration is hours or short minutes
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


def process_story(story_dir: str) -> bool:
    """Regenerate thumbnail.jpg for one story folder. Returns True on success."""
    meta_path = os.path.join(story_dir, "metadata.json")
    if not os.path.exists(meta_path):
        print(f"  ⚠  No metadata.json in {story_dir} — skipping")
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    movie_name = meta.get("original_name", "").replace(".txt", "").strip()
    duration_min = float(meta.get("estimated_duration_minutes", 180))

    if not movie_name:
        print(f"  ⚠  No original_name in {meta_path} — skipping")
        return False

    tagline = get_tagline(movie_name)
    dur_label = fmt_duration(duration_min)

    print(f"  🎬  {os.path.basename(story_dir)}: {movie_name} ({dur_label}) — {tagline}")

    # Fetch background
    bg = fetch_background(movie_name)

    # Apply overlay
    result = add_text_overlay(bg, movie_name, tagline, dur_label)

    # Save
    out_path = os.path.join(story_dir, "thumbnail.jpg")
    result.save(out_path, "JPEG", quality=95)
    print(f"    ✅  Saved: {out_path}")
    return True


def main():
    print("=" * 60)
    print("  Thumbnail Regenerator — ready_stories/")
    print("=" * 60)

    story_dirs = sorted([
        os.path.join(READY_DIR, d)
        for d in os.listdir(READY_DIR)
        if d.startswith("story_") and os.path.isdir(os.path.join(READY_DIR, d))
    ])

    success = 0
    for story_dir in story_dirs:
        try:
            if process_story(story_dir):
                success += 1
        except Exception as e:
            print(f"  ❌  Error on {os.path.basename(story_dir)}: {e}")

    print()
    print(f"Done: {success}/{len(story_dirs)} thumbnails regenerated.")


if __name__ == "__main__":
    main()
