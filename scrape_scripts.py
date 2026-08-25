import requests
from bs4 import BeautifulSoup
import os
import time

def scrape_movies(target_count=50):
    if not os.path.exists("pending_scripts"):
        os.makedirs("pending_scripts")
        
    print("Fetching IMSDb movie list...")
    r = requests.get("https://imsdb.com/all-scripts.html")
    soup = BeautifulSoup(r.text, 'html.parser')
    
    links = []
    for a in soup.find_all('a'):
        href = a.get('href')
        if href and '/Movie Scripts/' in href:
            links.append(href)
            
    print(f"Found {len(links)} total movies. Scraping {target_count}...")
    
    count = 0
    for link in links:
        if count >= target_count:
            break
            
        try:
            # Convert link to actual script page
            script_url = "https://imsdb.com" + link.replace("/Movie Scripts/", "/scripts/").replace(" Script.html", ".html").replace(" ", "-")
            movie_name = link.split("/Movie Scripts/")[-1].replace(" Script.html", "")
            
            print(f"[{count+1}/{target_count}] Downloading {movie_name}...")
            
            resp = requests.get(script_url)
            script_soup = BeautifulSoup(resp.text, 'html.parser')
            pre_tag = script_soup.find('pre')
            
            if pre_tag:
                script_text = pre_tag.text.strip()
                if len(script_text) > 1000:
                    safe_name = "".join(c for c in movie_name if c.isalnum() or c in " _-")
                    with open(f"pending_scripts/{safe_name}.txt", "w", encoding="utf-8", errors="ignore") as f:
                        f.write(script_text)
                    count += 1
            
            time.sleep(1) # Be nice to the server
        except Exception as e:
            print(f"Failed to download {link}: {e}")

if __name__ == "__main__":
    scrape_movies(100)
