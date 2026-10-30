"""Offline smoke checks for upload titles and both thumbnail layouts."""

from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

import youtube_uploader


def validate_ready_story_assets():
    tracked = subprocess.run(
        ["git", "ls-files", "ready_stories"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    story_dirs = sorted({Path(path).parent for path in tracked if path.endswith("metadata.json")})
    for story_dir in story_dirs:
        script = story_dir / "script.md"
        if not script.is_file() or script.stat().st_size <= 100:
            continue
        assets = {
            "story_art.jpg": (1280, 720),
            "thumbnail.jpg": (1280, 720),
            "short_thumbnail.jpg": (1080, 1920),
        }
        for name, expected_size in assets.items():
            path = story_dir / name
            if not path.is_file() or path.stat().st_size <= 10_000:
                raise AssertionError(f"Missing or undersized prebuilt asset: {path}")
            with Image.open(path) as image:
                if image.size != expected_size:
                    raise AssertionError(f"Unexpected image size for {path}: {image.size}")


def main():
    validate_ready_story_assets()

    title = youtube_uploader.format_youtube_title("The Hive's Lullaby", 354.6)
    assert title == "The Hive's Lullaby | 6-Hour Sleep Story", title
    assert len(title) <= 100
    short_title = youtube_uploader.format_short_youtube_title("The Hive's Lullaby", 50)
    assert short_title == "The Hive's Lullaby | 50-Second Sleep Story #Shorts", short_title
    assert len(short_title) <= 100

    def sample_background(movie_title, size=(1280, 720), story_description="", require_background=False):
        image = Image.new("RGB", size, (20, 33, 55))
        draw = ImageDraw.Draw(image)
        draw.rectangle((size[0] // 2, 0, size[0], size[1]), fill=(94, 110, 129))
        draw.ellipse((size[0] * .62, size[1] * .12, size[0] * .85, size[1] * .55), fill=(232, 183, 113))
        return image

    original_fetch = youtube_uploader._fetch_bg
    original_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    youtube_uploader._fetch_bg = sample_background
    try:
        with TemporaryDirectory() as temp_dir:
            summary_path = Path(temp_dir) / "github_summary.md"
            os.environ["GITHUB_STEP_SUMMARY"] = str(summary_path)
            assert youtube_uploader.append_related_video_action_summary(
                "long-video-id", "short-video-id", "The Hive's Lullaby"
            )
            summary = summary_path.read_text(encoding="utf-8")
            assert "long-video-id" in summary
            assert "short-video-id" in summary
            assert "Related video" in summary
            assert "studio.youtube.com/video/short-video-id/edit" in summary

            landscape_path = Path(temp_dir) / "landscape.jpg"
            art_path = Path(temp_dir) / "story_art.jpg"
            short_path = Path(temp_dir) / "short.jpg"
            youtube_uploader.generate_thumbnail(
                "The Hive's Lullaby",
                duration_minutes=354.6,
                output_path=str(landscape_path),
                story_description="Beneath the quiet metallic maze, a hidden chamber pulses with warmth.",
                art_output_path=str(art_path),
            )
            youtube_uploader.create_short_visual_frame(
                str(art_path), "The Hive's Lullaby", str(short_path)
            )

            with Image.open(landscape_path) as image:
                assert image.size == (1280, 720), image.size
            with Image.open(short_path) as image:
                assert image.size == (1080, 1920), image.size
            assert landscape_path.stat().st_size > 10_000
            assert short_path.stat().st_size > 10_000

    finally:
        youtube_uploader._fetch_bg = original_fetch
        if original_summary_path is None:
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
        else:
            os.environ["GITHUB_STEP_SUMMARY"] = original_summary_path

    print("Packaging validation passed: distinctive title, 16:9 thumbnail, 9:16 Shorts cover.")


if __name__ == "__main__":
    main()
