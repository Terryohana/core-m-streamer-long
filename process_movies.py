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

def _existing_story_titles():
    titles = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for folder in ("completed_stories", "ready_stories"):
        for path in glob.glob(os.path.join(base_dir, folder, "story_*", "metadata.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    title = json.load(f).get("title", "")
                if title:
                    titles.append(" ".join(str(title).split()))
            except (OSError, json.JSONDecodeError):
                continue
    return list(dict.fromkeys(titles))


def _usable_story_title(candidate, existing_titles):
    candidate = " ".join(str(candidate).replace('"', "").replace("'", "").split()).strip(" .:;|-—")
    words = re.findall(r"[A-Za-z0-9']+", candidate.lower())
    if not 3 <= len(words) <= 9 or len(candidate) > 68:
        return False
    cliches = {
        "velvet", "whisper", "whispers", "whispering", "echo", "echoes",
        "starlit", "starlight", "midnight", "silver", "golden", "hush",
        "lullaby", "dreamscape", "journey", "slumber", "sanctuary",
    }
    if cliches.intersection(words):
        return False
    normalized = candidate.casefold()
    return all(normalized != title.casefold() for title in existing_titles)


def generate_new_title(movie_name, story_description=""):
    title_rules = (
        "Write one catchy, explainer-style title for this specific story, 3–9 words. "
        "Make it sound like a gripping one-line premise: tell us who did what, what happened, "
        "or what dangerous choice/deal/setback makes this story intriguing. Use concrete story details "
        "and plain, natural language. A title may use a narrative hook such as 'The Night a Cop Saw the "
        "President’s Secret' or a compact character-and-stakes hook such as 'Two Grifters, One Dangerous "
        "Deal', but vary the wording and do not force either template. Avoid vague mood-only titles, "
        "ornamental adjective piles, generic poetic phrasing, and these overused words: velvet, whisper, echo, starlight, "
        "midnight, silver, golden, hush, lullaby, dreamscape, sanctuary. "
        "Do not copy the source movie title. Do not use a sleep-story suffix; the uploader adds it. "
        "Return only the title, without quotes or explanation."
    )
    existing_titles = _existing_story_titles()
    title_context = "\n".join(f"- {title}" for title in existing_titles[-60:])
    context = (
        f"Source inspiration: {movie_name}\nStory material: {story_description[:2200]}\n"
        f"Already-used story titles; do not repeat their phrases or opening pattern:\n{title_context}"
    )
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
                    {"role": "system", "content": title_rules},
                    {"role": "user", "content": context}
                ],
                "temperature": 0.8,
                "max_tokens": 50
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                candidate = resp.json()["choices"][0]["message"]["content"].strip()
                if _usable_story_title(candidate, existing_titles):
                    return candidate.strip('"\' ')
                print("CommandCode returned a repetitive or generic title; trying the fallback provider.")
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
                    {"role": "system", "content": title_rules},
                    {"role": "user", "content": context}
                ],
                "temperature": 0.8,
                "max_tokens": 50
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                candidate = resp.json()["choices"][0]["message"]["content"].strip()
                if _usable_story_title(candidate, existing_titles):
                    return candidate.strip('"\' ')
                print("Groq returned a repetitive or generic title; refusing to upload it.")
        except Exception:
            pass

    raise ValueError(
        f"No distinctive title passed quality checks for {movie_name}; "
        "review the story and provide a title before upload."
    )

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
            repurposed_title = generate_new_title(base_name, full_text)
            duration_minutes = len(final_audio_data) / 24000 / 60
            thumbnail_jpg = youtube_uploader.generate_thumbnail(
                repurposed_title,
                duration_minutes=duration_minutes,
                story_description=full_text[:1800],
            )
            final_mp4 = f"{base_name}_video.mp4"
            youtube_uploader.create_mp4(final_audio, thumbnail_jpg, final_mp4)
            
            # If the user has added the YOUTUBE_OAUTH_TOKEN secret, upload it!
            if os.environ.get("YOUTUBE_OAUTH_TOKEN"):
                yt_service = youtube_uploader.get_authenticated_service()
                
                upload_title = youtube_uploader.format_youtube_title(repurposed_title, duration_minutes)
                print(f"Prepared story title: '{upload_title}'")
                
                youtube_uploader.upload_video(
                    youtube=yt_service,
                    video_file=final_mp4,
                    title=upload_title,
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
    
    import youtube_uploader
    duration_minutes = float(meta.get("estimated_duration_minutes", 180))
    art_path = os.path.join(story_dir, "story_art.jpg")
    short_thumb = os.path.join(story_dir, "short_thumbnail.jpg")
    missing_assets = [path for path in (thumb_path, art_path, short_thumb) if not os.path.isfile(path)]
    if missing_assets:
        print(
            f"Missing prebuilt thumbnail assets for {story_dir}: {', '.join(os.path.basename(p) for p in missing_assets)}. "
            "Prepare them before running the GitHub Action.",
            flush=True,
        )
        return False
        
    print(f"Synthesizing audio for '{title}'...", flush=True)


    
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
    clean_script = re.sub(r'\[.*?\]', '', full_script).strip()
    
    print("Synthesizing audio with Kokoro TTS (Voice: am_michael, Speed: 1.25x)...", flush=True)
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np

    pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    
    # Split paragraphs for streaming Kokoro synthesis
    paragraphs = [p.strip() for p in clean_script.split('\n') if p.strip()]
    total_paras = len(paragraphs)
    print(f"Total script paragraphs to synthesize: {total_paras}", flush=True)
    
    temp_dir = os.path.join(story_dir, "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    start_tts = time.time()
    audio_chunks = []
    
    for idx, p_text in enumerate(paragraphs):
        for gs, ps, audio in pipeline(p_text, voice='am_michael', speed=1.25, split_pattern=r'\n+'):
            if audio is not None and len(audio) > 0:
                audio_chunks.append(audio)
        if (idx + 1) % 5 == 0 or (idx + 1) == total_paras:
            pct = round(((idx + 1) / total_paras) * 100, 1)
            print(f"[{idx+1}/{total_paras} ({pct}%)] Synthesizing audio paragraphs...", flush=True)

    master_wav = os.path.join(temp_dir, "master.wav")
    final_audio = os.path.join(story_dir, "audio.mp3")
    
    full_audio = np.concatenate(audio_chunks)
    sf.write(master_wav, full_audio, 24000)
    
    tts_elapsed = round(time.time() - start_tts, 1)
    print(f"All audio synthesized in {tts_elapsed} seconds! Converting to MP3 master track...", flush=True)
    
    # Convert master WAV to MP3 using ffmpeg
    subprocess.run([ffmpeg_exe, "-y", "-i", master_wav, "-codec:a", "libmp3lame", "-b:a", "192k", final_audio], check=True)
    
    # Cleanup temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except Exception:
        pass
        
    print(f"Master audio track generated successfully!", flush=True)
    
    # Video Encoding & YouTube Upload
    upload_state_path = os.path.join(story_dir, "youtube_upload_state.json")
    try:
        with open(upload_state_path, "r", encoding="utf-8") as state_file:
            upload_state = json.load(state_file)
    except (OSError, json.JSONDecodeError):
        upload_state = {}

    try:
        import youtube_uploader
        final_mp4 = os.path.join(story_dir, "video.mp4")
        short_mp4 = os.path.join(story_dir, "short.mp4")
        
        print(f"1. Encoding 1080p full-length MP4 video with ultra-fast FFmpeg engine...", flush=True)
        youtube_uploader.create_mp4(final_audio, thumb_path, final_mp4)
        upload_title = youtube_uploader.format_youtube_title(title, duration_minutes)
        
        print(f"2. Rendering 9:16 vertical Highlight Short with atmospheric artwork...", flush=True)
        try:
            youtube_uploader.create_short_mp4(
                final_audio,
                short_thumb,
                title,
                short_mp4,
                duration=50,
                story_description=description,
                prebuilt_frame=True,
            )
        except Exception as se:
            print(f"Short rendering encountered an issue (continuing with long video): {se}", flush=True)
            short_mp4 = None
        
        if os.environ.get("YOUTUBE_OAUTH_TOKEN"):
            print("Connecting to YouTube API...", flush=True)
            yt_service = youtube_uploader.get_authenticated_service()
            
            long_vid_id = upload_state.get("long_video_id")
            if not long_vid_id:
                # Step 1: Upload Full-Length Sleep Story Video
                print("Uploading Full-Length Sleep Story to YouTube...", flush=True)
                long_vid_id = youtube_uploader.upload_video(
                    youtube=yt_service,
                    video_file=final_mp4,
                    title=upload_title,
                    description=description,
                    thumbnail_path=thumb_path
                )
                upload_state["long_video_id"] = long_vid_id
                with open(upload_state_path, "w", encoding="utf-8") as state_file:
                    json.dump(upload_state, state_file, indent=2)
            else:
                print(f"Resuming upload with existing full-story video {long_vid_id}.", flush=True)
            
            # Step 2: Upload the matching 9:16 Short. YouTube's clickable
            # Shorts Related video field is not exposed by the Data API, so
            # upload_short records the exact Studio follow-up in Actions summary.
            if short_mp4 and os.path.exists(short_mp4):
                try:
                    if not upload_state.get("short_video_id"):
                        short_upload_title = youtube_uploader.format_short_youtube_title(
                            title, duration_seconds=60
                        )
                        print(f"Uploading Highlight Short paired with https://youtu.be/{long_vid_id}...", flush=True)
                        short_id = youtube_uploader.upload_short(
                            youtube=yt_service,
                            video_file=short_mp4,
                            title=short_upload_title,
                            long_video_id=long_vid_id,
                            thumbnail_path=short_thumb,
                        )
                        upload_state["short_video_id"] = short_id
                        with open(upload_state_path, "w", encoding="utf-8") as state_file:
                            json.dump(upload_state, state_file, indent=2)
                    else:
                        print(f"Resuming with existing Short {upload_state['short_video_id']}.", flush=True)
                except Exception as ue:
                    print(f"Short upload encountered an issue (main video uploaded OK): {ue}", flush=True)
        else:
            print("Skipping YouTube upload: YOUTUBE_OAUTH_TOKEN not set.", flush=True)
    except Exception as e:
        print(f"YouTube Upload Pipeline failed: {e}", flush=True)
        return False

    return bool(upload_state.get("long_video_id") and upload_state.get("short_video_id"))

def main():
    # 1. Check ready_stories queue first (strictly validated)
    candidate_dirs = sorted([d for d in glob.glob("ready_stories/story_*") if os.path.isdir(d)])
    ready_dirs = []
    for d in candidate_dirs:
        meta_path = os.path.join(d, "metadata.json")
        script_path = os.path.join(d, "script.md")
        if os.path.exists(meta_path) and os.path.exists(script_path):
            try:
                if os.path.getsize(script_path) > 100:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        json.load(f)
                    ready_dirs.append(d)
                else:
                    print(f"Skipping incomplete folder (empty script): {d}")
            except Exception as e:
                print(f"Skipping invalid package {d}: {e}")
        else:
            print(f"Skipping incomplete package {d} (missing metadata.json or script.md)")

    if ready_dirs:
        target_dir = ready_dirs[0]
        print(f"Found validated ready story package: {target_dir}")
        if not process_ready_story(target_dir):
            print(f"Upload incomplete; keeping {target_dir} in ready_stories for a safe retry.", flush=True)
            return
        
        os.makedirs("completed_stories", exist_ok=True)
        import shutil
        dest = os.path.join("completed_stories", os.path.basename(target_dir))
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.move(target_dir, dest)
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

