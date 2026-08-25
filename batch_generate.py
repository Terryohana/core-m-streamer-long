import os
import re
import glob
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "user_2trCechmdfT44LHrFP5rawqfM5KoExeGJeN1AWzyzMwWtcZhUgEoSepie3bdgGAKSAGAwpXNFKsQU7coZjLdpZgf"
MODEL = "google/gemini-3.5-flash-lite"
ENDPOINT = "https://api.commandcode.ai/provider/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def extract_text(filepath):
    if filepath.endswith('.srt'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        content = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
        content = re.sub(r'^\d+\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'<[^>]+>', '', content)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return " ".join(lines)
    else:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

def call_llm(messages, max_tokens=3000, temperature=0.7, retries=5):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    for attempt in range(retries):
        try:
            r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=45)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"[Attempt {attempt+1}] LLM status {r.status_code}: {r.text[:150]}", flush=True)
                time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f"[Attempt {attempt+1}] LLM error: {e}", flush=True)
            time.sleep(3 * (attempt + 1))
    raise Exception("LLM call failed after retries.")

def generate_title_and_description(original_name):
    system_prompt = (
        "You are a creative writer for a sleep story YouTube channel. "
        "Create a poetic, aesthetic bedtime story title and a relaxing 2-sentence description based on the mood of the given movie name. "
        "Do NOT mention or include the original movie title. "
        "Respond ONLY with valid JSON in this exact format: {\"title\": \"...\", \"description\": \"...\"}"
    )
    user_prompt = f"Movie name: {original_name}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    raw = call_llm(messages, max_tokens=150, temperature=0.8)
    try:
        clean_raw = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
        data = json.loads(clean_raw)
        return data.get("title", "Whispers of the Velvet Night"), data.get("description", "A calming, atmospheric sleep story.")
    except Exception:
        return "Whispers of the Velvet Night", "A calming, atmospheric sleep story designed to help you drift into deep rest."

def download_thumbnail(title, output_path):
    safe_prompt = requests.utils.quote(f"cinematic soothing ambient sleep scene for '{title}', starry night sky, cozy warm light, ultra peaceful, 8k, hyperrealistic, no text")
    image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
    for attempt in range(3):
        try:
            resp = requests.get(image_url, timeout=30)
            if resp.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            print(f"Thumbnail download attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(2)
    return False

def process_single_movie(script_path, story_dir, story_id):
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    os.makedirs(story_dir, exist_ok=True)
    
    script_file = os.path.join(story_dir, "script.md")
    thumb_file = os.path.join(story_dir, "thumbnail.jpg")
    meta_file = os.path.join(story_dir, "metadata.json")
    
    print(f"[{story_id}] Starting '{base_name}'...", flush=True)
    
    # 1. Title & Description
    repurposed_title, description = generate_title_and_description(base_name)
    print(f"[{story_id}] Retitled '{base_name}' -> '{repurposed_title}'", flush=True)
    
    # 2. Thumbnail
    print(f"[{story_id}] Generating thumbnail...", flush=True)
    download_thumbnail(repurposed_title, thumb_file)
    
    # 3. Read & Chunk
    full_text = extract_text(script_path)
    words = full_text.split()
    chunk_size = 500
    text_chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    total_chunks = len(text_chunks)
    
    print(f"[{story_id}] Full movie contains {len(words)} raw words in {total_chunks} scenes. Processing 100% in full...", flush=True)
    
    system_prompt = (
        "You are a master storyteller creating an immersive, full-length sleep story. "
        "Convert the provided movie dialogue into an expansive, continuous, third-person narrative. "
        "Make the prose deeply atmospheric, hypnotic, slow, and soothing. Describe the ambient lighting, gentle breezes, and quiet environments in rich, poetic detail. "
        "Format the output strictly with these exact speaker tags at the start of dialogue lines: [NARRATOR], [MALE], or [FEMALE]. "
        "Do not add any other tags."
    )
    
    full_script = ""
    previous_context = ""
    start_chunk = 0
    
    # Resume support if partial file exists
    if os.path.exists(script_file):
        with open(script_file, "r", encoding="utf-8") as f:
            existing = f.read()
        existing_chunks = len([c for c in existing.split("\n\n") if c.strip()])
        if existing_chunks > 0 and existing_chunks < total_chunks:
            print(f"[{story_id}] Resuming from chunk {existing_chunks + 1}/{total_chunks}...", flush=True)
            full_script = existing
            previous_context = existing[-300:]
            start_chunk = existing_chunks
            
    for idx in range(start_chunk, total_chunks):
        chunk = text_chunks[idx]
        user_prompt = f"Previous context:\n{previous_context}\n\nNext scene dialogue:\n{chunk}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        rewritten = call_llm(messages, max_tokens=3000)
        full_script += rewritten + "\n\n"
        previous_context = rewritten[-300:]
        print(f"[{story_id}] Scene {idx+1}/{total_chunks} rewritten ({len(full_script.split())} words so far)...", flush=True)
        
        # Save progress after every chunk
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(full_script)
            
    final_word_count = len(full_script.split())
    est_duration_minutes = round(final_word_count / 125, 1) # ~125 words per minute for slow sleep narration
    
    metadata = {
        "story_id": story_id,
        "original_name": base_name,
        "title": repurposed_title,
        "description": description,
        "tags": ["sleep story", "bedtime story", "relaxing audio", "sleep aid", "ambient storytelling", "full movie sleep story"],
        "scenes_processed": total_chunks,
        "total_words": final_word_count,
        "estimated_duration_minutes": est_duration_minutes,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"[{story_id}] COMPLETED: '{repurposed_title}' -> {final_word_count} words (~{est_duration_minutes} mins / {round(est_duration_minutes/60, 2)} hours of audio)", flush=True)
    return metadata

def run_batch(limit=8, max_workers=4):
    os.makedirs("ready_stories", exist_ok=True)
    script_files = sorted(glob.glob("pending_scripts/*.txt") + glob.glob("pending_scripts/*.srt"))[:limit]
    
    print(f"==================================================", flush=True)
    print(f"BATCH PROCESSOR: Processing first {len(script_files)} stories with {MODEL}", flush=True)
    print(f"==================================================", flush=True)
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, path in enumerate(script_files):
            story_id = f"story_{i+1:03d}"
            story_dir = os.path.join("ready_stories", story_id)
            future = executor.submit(process_single_movie, path, story_dir, story_id)
            futures[future] = story_id
            
        for future in as_completed(futures):
            story_id = futures[future]
            try:
                meta = future.result()
                results.append(meta)
            except Exception as e:
                print(f"ERROR in {story_id}: {e}", flush=True)
                
    manifest_path = os.path.join("ready_stories", "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total_stories": len(results), "stories": results}, f, indent=2)
        
    print(f"\n==================================================", flush=True)
    print(f"ALL {len(results)}/{len(script_files)} STORIES COMPLETED SUCCESSFULLY!", flush=True)
    print(f"Saved in ready_stories/ with manifest.json", flush=True)
    print(f"==================================================", flush=True)

if __name__ == "__main__":
    run_batch(limit=8, max_workers=4)
