import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time

MONGO_URI = os.getenv("MONGO_URI")
SCRAPER_API_KEY = "d1688c53992a7ff781b6e6de27a23f98"

def get_html(url, mode="standard"):
    """Multiple modes to bypass 500 errors"""
    print(f"🔄 Trying Mode: {mode}")
    
    # Mode settings
    params = {'api_key': SCRAPER_API_KEY, 'url': url}
    if mode == "premium":
        params['premium'] = 'true'
        params['country_code'] = 'us'
    elif mode == "render":
        params['render'] = 'true'
        params['premium'] = 'true'
    
    try:
        response = requests.get("http://api.scraperapi.com", params=params, timeout=120)
        return response
    except Exception as e:
        print(f"⚠️ Request failed in {mode}: {e}")
        return None

def run_scraper():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        target_url = "https://new4.hdhub4u.fo/"
        
        # --- PHASE 1: Try different ScraperAPI modes ---
        response = None
        for mode in ["premium", "render", "standard"]:
            res = get_html(target_url, mode)
            if res and res.status_code == 200:
                response = res
                print(f"✅ Success with {mode} mode!")
                break
            else:
                status = res.status_code if res else "No Response"
                print(f"❌ {mode} mode failed with status: {status}")

        if not response:
            print("💀 All ScraperAPI modes failed. HDHub is currently shielding too hard.")
            return

        # --- PHASE 2: Parsing (Same logic as before) ---
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main movie grid
        movie_items = soup.select('div.rt-movie-card') or \
                      soup.select('article') or \
                      soup.select('.post-item') or \
                      [a for a in soup.find_all('a') if a.find('img')]

        print(f"🔍 Found {len(movie_items)} potential items.")

        for item in movie_items:
            try:
                img_tag = item.find('img')
                link_tag = item if item.name == 'a' else item.find('a')
                
                if not img_tag or not link_tag: continue
                
                title = img_tag.get('alt') or img_tag.get('title') or ""
                link = link_tag.get('href')
                poster = img_tag.get('data-src') or img_tag.get('src')

                # Filter garbage
                if any(x in title.lower() for x in ['logo', 'app', 'telegram', 'join']): continue
                if len(title) < 5: continue

                if not collection.find_one({"title": title}):
                    collection.insert_one({
                        "title": title,
                        "poster": poster,
                        "source_link": link,
                        "status": "active",
                        "timestamp": time.time()
                    })
                    print(f"✅ Synced: {title}")
            except:
                continue

        print("🏁 Scraper finished.")

    except Exception as e:
        print(f"❌ Fatal: {e}")

if __name__ == "__main__":
    run_scraper()
