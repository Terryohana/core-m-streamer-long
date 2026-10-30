"""Prebuild the long-video and Shorts artwork for ready story packages."""

import argparse
import json
import time
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

import youtube_uploader


ROOT = Path(__file__).resolve().parent


def prepare_story(story_dir, force=False):
    metadata_path = story_dir / "metadata.json"
    if not metadata_path.is_file():
        return False
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    title = str(metadata.get("title", "A Peaceful Night's Sleep")).strip()
    description = str(metadata.get("description", "A calming, atmospheric sleep story."))
    duration = float(metadata.get("estimated_duration_minutes", 180))

    art_path = story_dir / "story_art.jpg"
    landscape_path = story_dir / "thumbnail.jpg"
    short_path = story_dir / "short_thumbnail.jpg"
    required = (art_path, landscape_path, short_path)
    if not force and all(path.is_file() for path in required):
        print(f"Already prepared: {story_dir.name}", flush=True)
        return True

    print(f"Preparing artwork for {story_dir.name}: {title}", flush=True)
    time.sleep(5)
    youtube_uploader.generate_thumbnail(
        title,
        duration_minutes=duration,
        output_path=str(landscape_path),
        story_description=description,
        art_output_path=str(art_path),
        require_background=True,
    )
    with Image.open(art_path) as art:
        if min(ImageStat.Stat(art).stddev) < 15:
            raise RuntimeError(f"Artwork lacks a distinct scene: {art_path}")
    youtube_uploader.create_short_visual_frame(
        str(art_path), title, str(short_path), description
    )
    return all(path.is_file() and path.stat().st_size > 10_000 for path in required)


def prepare_from_art(story_dir, source_art):
    """Build the three package assets from a supplied pre-generated scene image."""
    metadata = json.loads((story_dir / "metadata.json").read_text(encoding="utf-8"))
    title = str(metadata.get("title", "A Peaceful Night's Sleep")).strip()
    description = str(metadata.get("description", "A calming, atmospheric sleep story."))
    duration = float(metadata.get("estimated_duration_minutes", 180))
    art_path = story_dir / "story_art.jpg"
    landscape_path = story_dir / "thumbnail.jpg"
    short_path = story_dir / "short_thumbnail.jpg"
    with Image.open(source_art) as source:
        art = ImageOps.fit(source.convert("RGB"), (1280, 720), method=Image.Resampling.LANCZOS)
    art.save(art_path, "JPEG", quality=94)

    original_fetch = youtube_uploader._fetch_bg
    def use_prebuilt_art(_title, size=(1280, 720), story_description="", require_background=False):
        return art.resize(size, Image.Resampling.LANCZOS)
    youtube_uploader._fetch_bg = use_prebuilt_art
    try:
        youtube_uploader.generate_thumbnail(
            title,
            duration_minutes=duration,
            output_path=str(landscape_path),
            story_description=description,
            art_output_path=str(art_path),
            require_background=True,
        )
    finally:
        youtube_uploader._fetch_bg = original_fetch
    youtube_uploader.create_short_visual_frame(str(art_path), title, str(short_path), description)
    return all(path.is_file() and path.stat().st_size > 10_000 for path in (art_path, landscape_path, short_path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", help="Prepare one story folder name, such as story_070")
    parser.add_argument("--force", action="store_true", help="Regenerate existing artwork")
    parser.add_argument("--art", help="Use a pre-generated background image for the selected story")
    args = parser.parse_args()

    stories = [ROOT / "ready_stories" / args.story] if args.story else sorted(
        path for path in (ROOT / "ready_stories").glob("story_*") if path.is_dir()
    )
    failures = []
    if args.art:
        if len(stories) != 1:
            parser.error("--art requires --story")
        if not prepare_from_art(stories[0], args.art):
            raise SystemExit(f"Artwork missing or invalid for: {stories[0].name}")
        print(f"Prepared artwork from supplied image for {stories[0].name}.", flush=True)
        return
    for story_dir in stories:
        if not prepare_story(story_dir, force=args.force):
            failures.append(story_dir.name)
            print(f"Preparation failed: {story_dir}", flush=True)
    if failures:
        raise SystemExit(f"Artwork missing or invalid for: {', '.join(failures)}")
    print(f"Prepared {len(stories)} ready-story thumbnail packages.", flush=True)


if __name__ == "__main__":
    main()
