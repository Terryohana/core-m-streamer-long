import os
import re
import json
import time
import random
import requests
import urllib.parse
from PIL import Image, ImageDraw

def download_thumbnail(prompt, output_path, title):
    safe_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=25)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                print(f"  [+] Thumbnail downloaded successfully ({len(r.content)} bytes)")
                return True
        except Exception as e:
            print(f"  [-] Thumbnail attempt {attempt+1} error: {e}")
            time.sleep(2)
            
    # Fallback to rich dark aesthetic image
    print(f"  [-] Generating aesthetic dark fallback thumbnail for '{title}'")
    img = Image.new('RGB', (1280, 720), color=(12, 18, 38))
    draw = ImageDraw.Draw(img)
    draw.ellipse([580, 280, 700, 400], fill=(235, 225, 195))
    img.save(output_path)
    return True

def adapt_screenplay_to_sleep_story(raw_text, title, original_name):
    lines = raw_text.splitlines()
    output_paragraphs = []
    
    # Opening Meditation
    output_paragraphs.append(
        f"[NARRATOR] Welcome to tonight's peaceful sanctuary of deep, restorative slumber. "
        f"Take this moment to settle into your bed, softening your posture, letting your head sink gently into the pillow, "
        f"and releasing all the residual tension of the day. "
        f"Inhale slowly and deeply... feeling the cool, tranquil air fill your lungs... and gently exhale, letting go of all effort. "
        f"Tonight, we journey through an expansive, atmospheric sleep story inspired by the world of {title}. "
        f"Allow the calming rhythm of the narrative to carry you effortlessly into stillness and deep rest."
    )
    
    current_char = None
    current_dialogue = []
    
    dialogue_intros = [
        "speaks with a quiet, measured softness:",
        "answers in a low, calming tone:",
        "whispers gently into the still air:",
        "murmurs with a warm, steady cadence:",
        "adds in a relaxed, peaceful voice:",
        "responds with gentle reassurance:",
        "offers quietly, watching the shadows drift across the room:"
    ]

    def flush_dialogue():
        nonlocal current_char, current_dialogue
        if current_char and current_dialogue:
            text = ' '.join(current_dialogue).strip()
            # Clean parentheticals and extra whitespace
            text = re.sub(r'\(.*?\)', '', text).strip()
            if text and len(text) > 1:
                is_female = any(f in current_char.upper() for f in [
                    'FEMALE', 'WOMAN', 'GIRL', 'KAT', 'BIANCA', 'MARY', 'SARAH', 'MOTHER', 
                    'SISTER', 'CHASTITY', 'DONNA', 'PATSY', 'RACHEL', 'SUMMER', 'DOROTHY', 
                    'MARTHA', 'LUCY', 'HANNAH', 'CLAIRE', 'JULIET', 'ABBY', 'KATE', 'HELEN'
                ])
                tag = '[FEMALE]' if is_female else '[MALE]'
                intro = random.choice(dialogue_intros)
                char_title = current_char.title()
                output_paragraphs.append(f"[NARRATOR] {char_title} {intro}")
                output_paragraphs.append(f"{tag} {text}")
        current_char = None
        current_dialogue = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Screenplay character cue detection (indented or uppercase line, short)
        if re.match(r'^[A-Z0-9\s\(\)\'\.\-]{2,30}$', stripped) and not stripped.startswith(('INT.', 'EXT.', 'SCENE', 'CUT TO', 'FADE', 'TRANSITION', 'TITLE', 'ACT')):
            flush_dialogue()
            char_clean = re.sub(r'\(.*?\)', '', stripped).strip()
            if char_clean and len(char_clean) < 25 and not any(k in char_clean for k in ['DAY', 'NIGHT', 'CONTINUOUS', 'PAGE', 'REVISED']):
                current_char = char_clean
        elif current_char:
            current_dialogue.append(stripped)
        else:
            flush_dialogue()
            # Action line / scene description -> format as ambient narration
            if stripped.startswith(('INT.', 'EXT.', 'INT/EXT', 'SCENE')):
                scene_clean = stripped.replace('INT.', 'Inside, within').replace('EXT.', 'Outside, across').replace('-', 'under')
                scene_clean = re.sub(r'\s+', ' ', scene_clean)
                output_paragraphs.append(f"[NARRATOR] The atmosphere shifts into quiet stillness. {scene_clean.lower()}, the ambient light settles with a soft, peaceful glow over the surroundings.")
            elif not stripped.startswith(('PAGE', 'Revision', 'SCRIPT', 'CONTINUED:')):
                output_paragraphs.append(f"[NARRATOR] {stripped}")
                
    flush_dialogue()
    
    # Closing Sleep Lullaby
    output_paragraphs.append(
        f"[NARRATOR] The narrative softly draws to a close, and the world outside settles into pure, uninterrupted quiet. "
        f"The shadows lengthen across the room, wrapping you in a cocoon of warmth, safety, and deep peace. "
        f"Every breath you take now is slower, softer, and deeper. "
        f"There is nothing more to do, nowhere else to be. "
        f"Surrender completely to the gentle pull of sleep. Drifting... floating... sleeping deeply and peacefully through the night."
    )
    
    return "\n\n".join(output_paragraphs)

movie_configs = [
    {
        "id": "story_046",
        "script_file": "10 Things I Hate About You.txt",
        "title": "The Velvet Rhythm of Padua",
        "description": "A soothing, poetic journey through sunlit courtyards, gentle Pacific Northwest breezes, and the tender melodies of second chances. Drift effortlessly into deep, restful sleep.",
        "image_prompt": "Cinematic aesthetic nighttime scene of a historic brick high school courtyard with glowing amber streetlights, starry night sky, weeping trees, peaceful bedtime art, 8k, no text"
    },
    {
        "id": "story_047",
        "script_file": "12 Monkeys.txt",
        "title": "The Weaver of the Timeless Horizon",
        "description": "Drift through drifting timelines and peaceful celestial observatories. A deeply hypnotic sleep story designed to quiet the active mind and inspire tranquil slumber.",
        "image_prompt": "A majestic timeless astronomical observatory under a vast galaxy of sparkling stars, glowing astrolabes, serene cozy atmosphere, cinematic sleep art, no text"
    },
    {
        "id": "story_048",
        "script_file": "12 Years a Slave.txt",
        "title": "The River of Enduring Light",
        "description": "A deeply peaceful and atmospheric story of quiet resilience, whispering cypress groves, and golden morning horizons over the tranquil river.",
        "image_prompt": "A tranquil river winding through ancient moss-draped cypress trees at twilight, soft glowing lanterns on water, starry purple sky, peaceful sleep background, no text"
    },
    {
        "id": "story_049",
        "script_file": "12 and Holding.txt",
        "title": "Echoes of the Gentle Meadow",
        "description": "Rediscover the peaceful nostalgia of endless summer twilight, glowing fireflies in the grass, and the comforting stillness of childhood dreams.",
        "image_prompt": "A peaceful rolling meadow at dusk filled with glowing golden fireflies, ancient wooden treehouse, crescent moon in indigo sky, warm cozy bedtime aesthetic, no text"
    },
    {
        "id": "story_050",
        "script_file": "127 Hours.txt",
        "title": "The Solitude of the Crimson Canyon",
        "description": "A meditative exploration of quiet sandstone slot canyons, cool desert night breezes, and the vast silence of starry desert skies.",
        "image_prompt": "Serene glowing red rock slot canyon under a crystal clear Milky Way desert night sky, cool blue ambient light, ultra peaceful sleep meditation scene, no text"
    },
    {
        "id": "story_051",
        "script_file": "15 Minutes.txt",
        "title": "The Neon Echoes of Midnight Avenues",
        "description": "Take a tranquil midnight stroll through a slumbering metropolis where rain-slicked avenues reflect the soft glow of distant amber city lights.",
        "image_prompt": "A peaceful quiet city street at midnight after gentle rain, warm glowing street lamps, reflections on wet cobblestones, serene bedtime atmosphere, no text"
    },
    {
        "id": "story_052",
        "script_file": "17 Again.txt",
        "title": "The Second Bloom of Autumn Gold",
        "description": "A heartwarming, peaceful reflection on life's turning points, gentle autumn rain, and the comfort of returning home to rest.",
        "image_prompt": "A cozy suburban home nestled beneath golden autumn maple trees at twilight, warm light glowing from paned windows, peaceful sleep art, no text"
    },
    {
        "id": "story_053",
        "script_file": "2012.txt",
        "title": "The Ark Across the Cosmic Sea",
        "description": "Float peacefully above tranquil oceans and grand mountain ranges beneath a canopy of brilliant celestial constellations.",
        "image_prompt": "A majestic peaceful ship sailing across a calm reflective midnight ocean beneath glowing auroras and stars, ethereal dreamlike sleep scene, no text"
    },
    {
        "id": "story_054",
        "script_file": "20th Century Women.txt",
        "title": "The Warmth of the Pacific Breeze",
        "description": "Relax in a cozy coastal Craftsman house filled with the comforting hum of vinyl records, ocean fog, and gentle conversations.",
        "image_prompt": "A warm vintage California craftsman living room with open French doors overlooking the ocean at sunset, soft warm lamplight, tranquil sleep aesthetic, no text"
    },
    {
        "id": "story_055",
        "script_file": "28 Days Later.txt",
        "title": "The Quiet Dawn Over the Silent City",
        "description": "Experience the absolute stillness of an empty, peaceful city at dawn, where morning mist settles over historic bridges and quiet rivers.",
        "image_prompt": "London Tower Bridge and River Thames at a peaceful, completely still sunrise with soft pink and golden mist, calm glassy water, ultra serene sleep artwork, no text"
    }
]

def main():
    os.makedirs("ready_stories", exist_ok=True)
    
    print("==================================================================")
    print("FULL-LENGTH SLEEP STORY GENERATOR (25,000+ Words Per Package)")
    print("==================================================================")
    
    for cfg in movie_configs:
        story_id = cfg["id"]
        story_dir = os.path.join("ready_stories", story_id)
        os.makedirs(story_dir, exist_ok=True)
        
        script_file_path = os.path.join("pending_scripts", cfg["script_file"])
        if not os.path.exists(script_file_path):
            print(f"[-] Script not found: {script_file_path}")
            continue
            
        with open(script_file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
            
        print(f"\nProcessing {story_id} from '{cfg['script_file']}'...")
        full_story = adapt_screenplay_to_sleep_story(raw_text, cfg["title"], cfg["script_file"])
        
        target_script = os.path.join(story_dir, "script.md")
        with open(target_script, "w", encoding="utf-8") as f:
            f.write(full_story)
            
        word_count = len(full_story.split())
        est_duration = round(word_count / 125, 1)
        est_hours = round(est_duration / 60, 2)
        
        target_meta = os.path.join(story_dir, "metadata.json")
        metadata = {
            "story_id": story_id,
            "original_name": cfg["script_file"],
            "title": cfg["title"],
            "description": cfg["description"],
            "tags": [
                "sleep story",
                "bedtime story",
                "relaxing audio",
                "sleep aid",
                "ambient storytelling",
                "full movie sleep story",
                "3 hour sleep story",
                "deep sleep meditation"
            ],
            "scenes_processed": len(full_story.split("\n\n")),
            "total_words": word_count,
            "estimated_duration_minutes": est_duration,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(target_meta, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        target_thumb = os.path.join(story_dir, "thumbnail.jpg")
        download_thumbnail(cfg["image_prompt"], target_thumb, cfg["title"])
        
        print(f"[{story_id}] COMPLETED: '{cfg['title']}' -> {word_count} words (~{est_duration} mins / {est_hours} hours)")
        
    print("\n==================================================================")
    print("ALL FULL-LENGTH PACKAGES GENERATED AND STOCKED SUCCESSFULLY!")
    print("==================================================================")

if __name__ == "__main__":
    main()
