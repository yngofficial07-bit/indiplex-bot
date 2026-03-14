import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time

MONGO_URI = os.getenv("MONGO_URI")
SCRAPER_API_KEY = "d1688c53992a7ff781b6e6de27a23f98"

def run_scraper():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        # Hum seedha Bollywood section try karte hain, wahan cards zyada stable hote hain
        target_url = "https://new4.hdhub4u.fo/category/bollywood-movies/"
        
        print(f"🚀 Scanning Bollywood Category: {target_url}")
        
        # Premium + Render (Taki images load ho jayein)
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true&render=true"
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- THE MASTER SCAN ---
            # Hum saare 'a' tags nikalenge jinke andar 'img' hai
            potential_movies = [a for a in soup.find_all('a') if a.find('img')]
            print(f"🔍 Found {len(potential_movies)} raw image-links.")

            count = 0
            for item in potential_movies:
                try:
                    img_tag = item.find('img')
                    link = item.get('href')
                    
                    # 1. Title nikalna (Alt ya Title attribute se)
                    title = img_tag.get('alt') or img_tag.get('title') or ""
                    # 2. Poster URL nikalna
                    poster = img_tag.get('data-src') or img_tag.get('src') or ""

                    # --- JORDAR FILTERS ---
                    # Faltu cheezein skip karo
                    garbage = ['logo', 'android', 'app', 'telegram', 'group', 'join', 'banner', 'click', 'dmca']
                    if any(x in title.lower() for x in garbage) or not title:
                        continue
                    
                    # Sirf wahi links lo jo lambe hain (asli movie posts)
                    if len(title) < 10 or "http" not in link:
                        continue

                    # 3. Database Check & Sync
                    if not collection.find_one({"title": title}):
                        collection.insert_one({
                            "title": title,
                            "poster": poster,
                            "source_link": link,
                            "status": "active",
                            "timestamp": time.time()
                        })
                        print(f"✅ MOVIE SYNCED: {title}")
                        count += 1
                    else:
                        print(f"⏩ Skipping Duplicate: {title[:20]}...")
                except:
                    continue
            
            print(f"🏁 Done! Total Movies Added: {count}")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
