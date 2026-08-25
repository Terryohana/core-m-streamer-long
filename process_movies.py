import os
import re
import requests
import soundfile as sf
import numpy as np
from kokoro import KPipeline
import time
import glob

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def extract_text_from_srt(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    content = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
    content = re.sub(r'^\d+\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'<[^>]+>', '', content)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return " ".join(lines)

def rewrite_chunk_groq(chunk_text, previous_context=""):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are a master storyteller. We are converting a movie script into an atmospheric sleep story.
Format the output strictly with these exact speaker tags at the start of dialogue lines: [NARRATOR], [MALE], or [FEMALE]. Do not add any other tags.
Make the prose incredibly soothing, slow, and hypnotic. Convert the provided movie dialogue into a continuous third-person narrative."""

    user_prompt = f"""Previous context (for continuity):
{previous_context}

Next dialogue to rewrite:
{chunk_text}
"""

    payload = {
        "model": "qwen/qwen3.6-27b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    for attempt in range(50):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                error_msg = resp.text
                print(f"Groq API returned status {resp.status_code}: {error_msg}")
                if resp.status_code == 429:
                    # Extract wait time from Groq's error message (e.g., "Please try again in 23m6.7s")
                    import re
                    match = re.search(r'try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?', error_msg)
                    if match:
                        h = float(match.group(1)) if match.group(1) else 0
                        m = float(match.group(2)) if match.group(2) else 0
                        s = float(match.group(3)) if match.group(3) else 0
                        sleep_time = (h * 3600) + (m * 60) + s + 5 # Add 5 seconds buffer
                        print(f"Daily Limit Hit! Sleeping for {sleep_time/60:.1f} minutes...")
                        time.sleep(sleep_time)
                        continue
                        
                if resp.status_code in [429, 503, 500]:
                    sleep_time = 30 * (attempt + 1)
                    print(f"Waiting {sleep_time} seconds before retry...")
                    time.sleep(sleep_time)
                else:
                    break
        except Exception as e:
            print(f"Groq API error: {e}")
            time.sleep(30 * (attempt + 1))
    raise Exception("Groq API failed after 50 attempts.")

def generate_new_title(movie_name):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen/qwen3.6-27b",
        "messages": [
            {"role": "system", "content": "You are a creative writer. Generate a very short, poetic, aesthetic sleep story title inspired by the vibe of the given movie name. Do not include the original movie name. Output ONLY the title, nothing else. Example: 'Echoes of the Midnight Stars'"},
            {"role": "user", "content": f"Movie: {movie_name}"}
        ],
        "temperature": 0.8,
        "max_tokens": 50
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        return resp.json()["choices"][0]["message"]["content"].replace('"', '').strip()
    except Exception:
        return "Whispers of the Deep Night"

def process_movie(script_file):
    base_name = os.path.splitext(os.path.basename(script_file))[0]
    script_output = f"{base_name}_script.md"
    final_audio = f"{base_name}_audio.wav"
    
    if os.path.exists(final_audio):
        print(f"Skipping {script_file}, audio already generated.")
        return
        
    print(f"Reading {script_file}...")
    if script_file.endswith('.srt'):
        full_text = extract_text_from_srt(script_file)
    else:
        with open(script_file, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()
            
    words = full_text.split()
    
    chunk_size = 500
    text_chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    print(f"Total words: {len(words)}. Splitting into {len(text_chunks)} chunks.")
    
    full_script = ""
    previous_context = ""
    start_chunk = 0
    
    if os.path.exists(script_output):
        with open(script_output, "r", encoding="utf-8") as f:
            existing = f.read()
        chunks_done = len(existing.split("\n\n")) - 1
        if chunks_done > 0:
            print(f"Resuming from chunk {chunks_done + 1}...")
            full_script = existing
            previous_context = existing[-200:] if len(existing) > 200 else existing
            start_chunk = chunks_done

    for i in range(start_chunk, len(text_chunks)):
        chunk = text_chunks[i]
        print(f"Rewriting chunk {i+1}/{len(text_chunks)} via Groq...")
        rewritten = rewrite_chunk_groq(chunk, previous_context)
        full_script += rewritten + "\n\n"
        previous_context = rewritten[-200:]
        
        with open(script_output, "w", encoding="utf-8") as f:
            f.write(full_script)
            
    print("Writing finished! Initializing Kokoro TTS...")
    pipeline = KPipeline(lang_code='a') 
    audio_segments = []
    
    full_script = re.sub(r'<think>.*?</think>', '', full_script, flags=re.DOTALL)
    
    lines = full_script.split('\n')
    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        voice = 'af_bella'
        if line.startswith('[NARRATOR]'):
            voice = 'af_nicole' 
            line = line.replace('[NARRATOR]', '').strip()
        elif line.startswith('[MALE]'):
            voice = 'am_adam'
            line = line.replace('[MALE]', '').strip()
        elif line.startswith('[FEMALE]'):
            voice = 'af_bella'
            line = line.replace('[FEMALE]', '').strip()
        else:
            voice = 'af_nicole'
            
        if not line:
            continue
            
        print(f"[{line_idx+1}/{len(lines)}] Rendering {voice}: {line[:50]}...")
        try:
            generator = pipeline(line, voice=voice, speed=1.25, split_pattern=r'\n+')
            for _, _, audio in generator:
                audio_segments.append(audio)
        except Exception as e:
            print(f"Error rendering line: {e}")

    print("Concatenating and saving...")
    if audio_segments:
        final_audio_data = np.concatenate(audio_segments)
        sf.write(final_audio, final_audio_data, 24000)
        print(f"Final audio saved to {final_audio}")
        
        # --- YouTube Auto-Upload Pipeline ---
        try:
            import youtube_uploader
            thumbnail_jpg = youtube_uploader.generate_thumbnail(base_name)
            final_mp4 = f"{base_name}_video.mp4"
            youtube_uploader.create_mp4(final_audio, thumbnail_jpg, final_mp4)
            
            # If the user has added the YOUTUBE_OAUTH_TOKEN secret, upload it!
            if os.environ.get("YOUTUBE_OAUTH_TOKEN"):
                yt_service = youtube_uploader.get_authenticated_service()
                
                # Generate a brand new, repurposed sleep title!
                repurposed_title = generate_new_title(base_name)
                print(f"Renamed '{base_name}' to new title: '{repurposed_title}'")
                
                youtube_uploader.upload_video(
                    youtube=yt_service,
                    video_file=final_mp4,
                    title=repurposed_title,
                    description=f"Drift off to a deeply relaxing, atmospheric sleep story. Close your eyes, slow your breathing, and let the narrative guide you to a restful night's sleep.",
                    thumbnail_path=thumbnail_jpg
                )
            else:
                print("Skipping YouTube upload: YOUTUBE_OAUTH_TOKEN not set.")
                
        except Exception as e:
            print(f"YouTube Upload Pipeline failed: {e}")
            
    else:
        print("No audio was generated!")

def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY environment variable not set.")
        return
        
    if not os.path.exists("pending_scripts"):
        print("No pending_scripts directory found.")
        return
        
    if not os.path.exists("completed_scripts"):
        os.makedirs("completed_scripts")
        
    scripts = glob.glob("pending_scripts/*.srt") + glob.glob("pending_scripts/*.txt")
    if not scripts:
        print("No scripts found in the pending_scripts directory.")
        return
        
    # Only process ONE movie per run so we upload once a day
    target_script = scripts[0]
    print(f"Processing script for today: {target_script}")
    
    process_movie(target_script)
    
    # Move it to completed
    import shutil
    shutil.move(target_script, os.path.join("completed_scripts", os.path.basename(target_script)))
    print("Script moved to completed_scripts/")

if __name__ == "__main__":
    main()
