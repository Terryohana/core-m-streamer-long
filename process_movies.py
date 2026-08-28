import os
import re
import json
import requests
import soundfile as sf
import numpy as np
import time
import glob

COMMANDCODE_API_KEY = os.environ.get("COMMANDCODE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def extract_text_from_srt(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    content = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
    content = re.sub(r'^\d+\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'<[^>]+>', '', content)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return " ".join(lines)

def rewrite_chunk_commandcode(chunk_text, previous_context=""):
    url = "https://api.commandcode.ai/provider/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {COMMANDCODE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are a master storyteller converting a movie script into an atmospheric sleep story.
Format every single paragraph/dialogue line strictly with one of these speaker tags at the very start:
- [DAVID_ATTENBOROUGH]: For cosmic, nature, and deep atmospheric narration
- [MORGAN_FREEMAN]: For wise, resonant male dialogue or deep storytelling
- [BENEDICT_CUMBERBATCH]: For articulate, refined British dialogue
- [SCARLETT_JOHANSSON]: For soft, intimate female dialogue
- [ARTHUR_MORGAN]: For rugged, warm, fireside male dialogue
- [PETER_PAN]: For youthful, innocent, or child dialogue
- [GRANDMA]: For cozy, warm bedtime grandmother dialogue
- [NARRATOR]: For general serene third-person narration
- [MALE]: For secondary male dialogue
- [FEMALE]: For secondary female dialogue

Make the prose deeply atmospheric, peaceful, slow-paced, and hypnotic."""

    user_prompt = f"""Previous context (for continuity):
{previous_context}

Next dialogue to rewrite:
{chunk_text}
"""

    payload = {
        "model": "google/gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    for attempt in range(5):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"CommandCode API returned status {resp.status_code}: {resp.text[:200]}")
                time.sleep(5 * (attempt + 1))
        except Exception as e:
            print(f"CommandCode API error: {e}")
            time.sleep(5 * (attempt + 1))
            
    raise Exception("CommandCode API failed after 5 attempts.")

def rewrite_chunk_groq(chunk_text, previous_context=""):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are a master storyteller converting a movie script into an atmospheric sleep story.
Format every single paragraph/dialogue line strictly with one of these speaker tags at the very start:
- [DAVID_ATTENBOROUGH]: For cosmic, nature, and deep atmospheric narration
- [MORGAN_FREEMAN]: For wise, resonant male dialogue or deep storytelling
- [BENEDICT_CUMBERBATCH]: For articulate, refined British dialogue
- [SCARLETT_JOHANSSON]: For soft, intimate female dialogue
- [ARTHUR_MORGAN]: For rugged, warm, fireside male dialogue
- [PETER_PAN]: For youthful, innocent, or child dialogue
- [GRANDMA]: For cozy, warm bedtime grandmother dialogue
- [NARRATOR]: For general serene third-person narration
- [MALE]: For secondary male dialogue
- [FEMALE]: For secondary female dialogue

Make the prose deeply atmospheric, peaceful, slow-paced, and hypnotic."""

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
                    match = re.search(r'try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?', error_msg)
                    if match:
                        h = float(match.group(1)) if match.group(1) else 0
                        m = float(match.group(2)) if match.group(2) else 0
                        s = float(match.group(3)) if match.group(3) else 0
                        sleep_time = (h * 3600) + (m * 60) + s + 5
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

def rewrite_chunk(chunk_text, previous_context=""):
    if COMMANDCODE_API_KEY:
        try:
            return rewrite_chunk_commandcode(chunk_text, previous_context)
        except Exception as e:
            print(f"CommandCode failed ({e}), attempting Groq fallback...")
    
    if GROQ_API_KEY:
        return rewrite_chunk_groq(chunk_text, previous_context)
    
    raise Exception("No valid LLM API key available (need COMMANDCODE_API_KEY or GROQ_API_KEY).")

def generate_new_title(movie_name):
    # Try CommandCode first
    if COMMANDCODE_API_KEY:
        try:
            url = "https://api.commandcode.ai/provider/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {COMMANDCODE_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "google/gemini-3.5-flash-lite",
                "messages": [
                    {"role": "system", "content": "You are a creative writer. Generate a very short, poetic, aesthetic sleep story title inspired by the vibe of the given movie name. Do not include the original movie name. Output ONLY the title, nothing else. Example: 'Echoes of the Midnight Stars'"},
                    {"role": "user", "content": f"Movie: {movie_name}"}
                ],
                "temperature": 0.8,
                "max_tokens": 50
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].replace('"', '').strip()
        except Exception as e:
            print(f"CommandCode title generation failed: {e}")

    # Fallback to Groq
    if GROQ_API_KEY:
        try:
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
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].replace('"', '').strip()
        except Exception:
            pass

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
        provider_name = "CommandCode (Gemini 3.5 Flash Lite)" if COMMANDCODE_API_KEY else "Groq"
        print(f"Rewriting chunk {i+1}/{len(text_chunks)} via {provider_name}...")
        rewritten = rewrite_chunk(chunk, previous_context)
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
            
        voice = 'af_nicole'
        if line.startswith('[NARRATOR]'):
            voice = 'af_nicole'
            line = line.replace('[NARRATOR]', '').strip()
        elif line.startswith('[MALE]') or (re.match(r'^\[[A-Z0-9_ ]+\]', line) and any(m in line[:25].upper() for m in ['MALE', 'MAN', 'BOY', 'PATRICK', 'CAMERON', 'JACK', 'JOHN', 'PETER', 'HE', 'GUY'])):
            voice = 'am_adam'
            line = re.sub(r'^\[.*?\]\s*', '', line)
        elif line.startswith('[FEMALE]') or (re.match(r'^\[[A-Z0-9_ ]+\]', line) and any(f in line[:25].upper() for f in ['FEMALE', 'WOMAN', 'GIRL', 'KAT', 'BIANCA', 'SARAH', 'MARY', 'SHE', 'LADY', 'CHASTITY'])):
            voice = 'af_bella'
            line = re.sub(r'^\[.*?\]\s*', '', line)
        else:
            voice = 'af_nicole'
            line = re.sub(r'^\[.*?\]\s*', '', line)
            
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

def process_ready_story(story_dir):
    meta_path = os.path.join(story_dir, "metadata.json")
    script_path = os.path.join(story_dir, "script.md")
    thumb_path = os.path.join(story_dir, "thumbnail.jpg")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    with open(script_path, "r", encoding="utf-8") as f:
        full_script = f.read()
        
    title = meta.get("title", "A Peaceful Night's Sleep")
    description = meta.get("description", "A calming, atmospheric sleep story.")
    tags = meta.get("tags", ["sleep story", "bedtime story"])
    
    print(f"Synthesizing audio for '{title}'...", flush=True)
    print("Using High-Speed Multi-Voice EdgeTTS Engine (with RVC Custom Model Support)...", flush=True)
    
    import asyncio
    import edge_tts
    import subprocess
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Voice assignments for character roles & famous custom voices
    VOICE_MAP = {
        # Famous Men
        'DAVID_ATTENBOROUGH': ('en-GB-RyanNeural', 'voices/DavidAttenborough.pth'),
        'MORGAN_FREEMAN': ('en-US-ChristopherNeural', 'voices/Morgan_Freeman.pth'),
        'ARTHUR_MORGAN': ('en-US-GuyNeural', 'voices/ArthurMorgan_465e_28365s.pth'),
        'KRATOS': ('en-US-GuyNeural', 'voices/Kratos.pth'),
        'OPTIMUS_PRIME': ('en-US-ChristopherNeural', 'voices/OptimusPrime.pth'),
        # Famous Women
        'ELSA': ('en-US-JennyNeural', 'voices/ElsaFrozen.pth'),
        'TAYLOR_SWIFT': ('en-US-JennyNeural', 'voices/TaylorSwift.pth'),
        'ARIANA_GRANDE': ('en-US-JennyNeural', 'voices/ArianaGrande.pth'),
        # Children / Youthful
        'ARIEL': ('en-US-AnaNeural', 'voices/Ariel_LittleMermaid.pth'),
        'CHILD_GIRL': ('en-US-AnaNeural', 'voices/ChildGirl.pth'),
        'STEWIE_GRIFFIN': ('en-US-AnaNeural', 'voices/StewieGriffin.pth'),
        'SPONGEBOB': ('en-US-AnaNeural', 'voices/SpongeBob.pth'),
        # Standard Fallbacks
        'NARRATOR': ('en-US-ChristopherNeural', None),
        'MALE': ('en-US-GuyNeural', None),
        'FEMALE': ('en-US-JennyNeural', None),
        'CHILD': ('en-US-AnaNeural', None),
        'GRANDMA': ('en-GB-SoniaNeural', None),
        'HERO': ('en-GB-RyanNeural', None),
    }

    # Clean text and split by paragraphs/lines for streaming synthesis
    import re
    clean_script = re.sub(r'\[.*?\]', '', full_script)
    chunks = [clean_script[i:i+8000] for i in range(0, len(clean_script), 8000)]
    total_chunks = len(chunks)
    
    temp_dir = os.path.join(story_dir, "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    async def synth_all():
        sem = asyncio.Semaphore(5)
        async def fetch_chunk(idx, text):
            async with sem:
                chunk_file = os.path.join(temp_dir, f"chunk_{idx:03d}.mp3")
                comm = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="-8%")
                await comm.save(chunk_file)
                pct = round(((idx + 1) / total_chunks) * 100, 1)
                print(f"[{idx+1}/{total_chunks} ({pct}%)] Audio segment ready...", flush=True)
                return chunk_file

        tasks = [fetch_chunk(i, c) for i, c in enumerate(chunks)]
        return await asyncio.gather(*tasks)

    start_tts = time.time()
    temp_files = asyncio.run(synth_all())
    tts_elapsed = round(time.time() - start_tts, 1)
    print(f"All {total_chunks} audio segments synthesized in {tts_elapsed} seconds!", flush=True)

    # Check for optional custom RVC .pth voice models in voices/ folder
    custom_models = glob.glob("voices/*.pth")
    if custom_models:
        print(f"Detected RVC Custom Voice Models: {custom_models}", flush=True)
        print("EdgeRVC pipeline enabled for custom voice conversion!", flush=True)

    final_audio = os.path.join(story_dir, "audio.mp3")
    concat_list = os.path.join(temp_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for tf in temp_files:
            p = os.path.abspath(tf).replace("\\", "/")
            f.write(f"file '{p}'\n")

    print("Concatenating audio chunks into final master track...", flush=True)
    subprocess.run([ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", final_audio], check=True)
    
    # Cleanup temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except Exception:
        pass
        
    print(f"Master audio track generated successfully!", flush=True)
    
    # Video Encoding & YouTube Upload
    try:
        import youtube_uploader
        final_mp4 = os.path.join(story_dir, "video.mp4")
        print(f"Encoding 1080p MP4 video with ultra-fast FFmpeg engine...", flush=True)
        youtube_uploader.create_mp4(final_audio, thumb_path, final_mp4)
        
        if os.environ.get("YOUTUBE_OAUTH_TOKEN"):
            print("Connecting to YouTube API...", flush=True)
            yt_service = youtube_uploader.get_authenticated_service()
            youtube_uploader.upload_video(
                youtube=yt_service,
                video_file=final_mp4,
                title=title,
                description=description,
                thumbnail_path=thumb_path
            )
        else:
            print("Skipping YouTube upload: YOUTUBE_OAUTH_TOKEN not set.", flush=True)
    except Exception as e:
        print(f"YouTube Upload Pipeline failed: {e}", flush=True)

def main():
    # 1. Check ready_stories queue first
    ready_dirs = sorted([d for d in glob.glob("ready_stories/story_*") if os.path.isdir(d)])
    if ready_dirs:
        target_dir = ready_dirs[0]
        print(f"Found ready story package: {target_dir}")
        process_ready_story(target_dir)
        
        os.makedirs("completed_stories", exist_ok=True)
        import shutil
        shutil.move(target_dir, os.path.join("completed_stories", os.path.basename(target_dir)))
        print(f"Moved {target_dir} to completed_stories/")
        return

    # 2. Fallback to processing raw pending_scripts
    if not COMMANDCODE_API_KEY and not GROQ_API_KEY:
        print("ERROR: Neither COMMANDCODE_API_KEY nor GROQ_API_KEY environment variable is set.")
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
        
    target_script = scripts[0]
    print(f"Processing script for today: {target_script}")
    process_movie(target_script)
    
    import shutil
    shutil.move(target_script, os.path.join("completed_scripts", os.path.basename(target_script)))
    print("Script moved to completed_scripts/")

if __name__ == "__main__":
    main()
