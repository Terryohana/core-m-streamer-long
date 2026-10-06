import os
import json
import subprocess
import requests
import urllib.parse

COMMIT = "325eae73ade9d3193fa805583225310c50d748b3"

stories_mapping = [
    {
        "target_id": "story_047",
        "source_id": "story_042",
        "movie_name": "Air Force One",
        "title": "Whispers Above the Midnight Stratosphere",
        "description": "Drift into the quiet realm high above the slumbering world where the gentle, rhythmic hum of engines lulls the wandering mind. Let the stillness of the upper skies carry you into deep and peaceful rest.",
        "thumb_fallback_prompt": "Cinematic soothing airplane flying above soft clouds at midnight beneath stars, peaceful ambient blue and gold lighting, ultra relaxing sleep background, no text"
    },
    {
        "target_id": "story_048",
        "source_id": "story_043",
        "movie_name": "Air",
        "title": "The Quiet Architect of Flight",
        "description": "Drift back to the quiet, dew-kissed afternoons of Oregon where dreams are quietly stitched into reality. Let the soothing rhythm of unhurried conversations guide you into restful slumber.",
        "thumb_fallback_prompt": "Peaceful misty morning in Oregon pine forest, warm golden amber sunbeams, quiet cozy vintage office window, serene sleep art, no text"
    },
    {
        "target_id": "story_049",
        "source_id": "story_044",
        "movie_name": "Airplane!",
        "title": "The Serene Navigator of the Cloudscape",
        "description": "Float effortlessly among endless silver clouds beneath the soft amber glow of midnight instrument lights. Let the gentle expanse of the night sky guide you into peaceful slumber.",
        "thumb_fallback_prompt": "Majestic cockpit looking out over an ocean of calm clouds and Milky Way galaxy at night, soft warm instrument glow, peaceful bedtime aesthetic, no text"
    },
    {
        "target_id": "story_050",
        "source_id": "story_045",
        "movie_name": "Aladdin",
        "title": "Whispers of the Velvet Sands",
        "description": "Drift across undulating golden dunes where cool evening breezes carry the faint melody of ancient desert nights. Surrender to the starlit stillness of an Arabian dreamscape.",
        "thumb_fallback_prompt": "Serene Arabian desert palace under glowing starlit sky, rolling purple and golden dunes, warm lanterns, peaceful sleep art, no text"
    },
    {
        "target_id": "story_051",
        "source_id": "story_046",
        "movie_name": "One Night in Miami",
        "title": "Echoes in the Velvet Night of the Palms",
        "description": "Settle into the warm, tranquil air of a tropical haven where gentle conversations float softly through the swaying palm trees. Let the peaceful night breeze wrap you in soothing rest.",
        "thumb_fallback_prompt": "A warm cozy Miami courtyard at night, silhouetted palm trees against deep violet twilight, warm amber patio glow, peaceful bedtime scene, no text"
    },
    {
        "target_id": "story_052",
        "source_id": "story_047",
        "movie_name": "Alien 3",
        "title": "The Foundry of Still Waters",
        "description": "Drift into the profound, meditative quiet of an ancient stone sanctuary surrounded by the gentle warmth of glowing embers and quiet waters. Let the peaceful stillness cradle you into sleep.",
        "thumb_fallback_prompt": "Ancient stone monastery foundry with gentle glowing amber hearth, calm water reflecting moonlight, starry night sky, ultra peaceful sleep art, no text"
    }
]

def main():
    os.makedirs("ready_stories", exist_ok=True)
    
    # Clean out current ready_stories
    import shutil
    for d in os.listdir("ready_stories"):
        full_d = os.path.join("ready_stories", d)
        if os.path.isdir(full_d):
            shutil.rmtree(full_d)
            
    print("Cleaned ready_stories directory. Restoring genuine original-batch movie stories...")
    
    for item in stories_mapping:
        target_dir = os.path.join("ready_stories", item["target_id"])
        os.makedirs(target_dir, exist_ok=True)
        
        # 1. Extract original script.md
        src_script_path = f"ready_stories/{item['source_id']}/script.md"
        script_content = subprocess.check_output(
            ["git", "show", f"{COMMIT}:{src_script_path}"],
            text=True,
            encoding="utf-8"
        )
        
        dest_script = os.path.join(target_dir, "script.md")
        with open(dest_script, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        word_count = len(script_content.split())
        est_duration = round(word_count / 125, 1)
        
        # 2. Extract or generate thumbnail.jpg
        src_thumb_path = f"ready_stories/{item['source_id']}/thumbnail.jpg"
        dest_thumb = os.path.join(target_dir, "thumbnail.jpg")
        thumb_saved = False
        try:
            thumb_bytes = subprocess.check_output(
                ["git", "show", f"{COMMIT}:{src_thumb_path}"]
            )
            if len(thumb_bytes) > 1000:
                with open(dest_thumb, "wb") as f:
                    f.write(thumb_bytes)
                thumb_saved = True
                print(f"  [+] Restored original thumbnail from git ({len(thumb_bytes)} bytes)")
        except Exception:
            pass
            
        if not thumb_saved:
            print(f"  [-] Downloading thumbnail for {item['title']}...")
            try:
                safe_p = urllib.parse.quote(item["thumb_fallback_prompt"])
                r = requests.get(f"https://image.pollinations.ai/prompt/{safe_p}?width=1280&height=720&nologo=true", timeout=20)
                if r.status_code == 200 and len(r.content) > 1000:
                    with open(dest_thumb, "wb") as f:
                        f.write(r.content)
                    thumb_saved = True
            except Exception as e:
                print(f"  [-] Thumbnail download failed: {e}")
                
        # 3. Create metadata.json
        metadata = {
            "story_id": item["target_id"],
            "original_name": item["movie_name"],
            "title": item["title"],
            "description": item["description"],
            "tags": [
                "sleep story",
                "bedtime story",
                "relaxing audio",
                "sleep aid",
                "ambient storytelling",
                "full movie sleep story"
            ],
            "scenes_processed": len(script_content.split("\n\n")),
            "total_words": word_count,
            "estimated_duration_minutes": est_duration,
            "created_at": "2026-10-06 09:00:00"
        }
        
        with open(os.path.join(target_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"[{item['target_id']}] RESTORED: '{item['title']}' ({item['movie_name']}) -> {word_count} words (~{est_duration} mins / {round(est_duration/60, 2)} hrs)")
        
    print("\nAll 6 original movie sleep stories restored successfully!")

if __name__ == "__main__":
    main()
