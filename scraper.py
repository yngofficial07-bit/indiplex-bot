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

        # Domain change to .icu (HDHub mirrors are often less protected)
        target_url = "https://hdhub4u.icu/" 
        
        # Using premium proxies without heavy rendering to avoid 500
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true&country_code=in"
        
        print(f"🚀 Shadow Scraper targeting: {target_url}")
        
        # Headers to look even more human
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        
        response = requests.get(proxy_url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            print("✅ Connection Successful! Parsing HTML...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Universal Hunter: Looking for any link that looks like a movie
            links = soup.find_all('a')
            print(f"📡 Found {len(links)} links. Filtering for movies...")
            
            count = 0
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # HDHub typical patterns
                if any(word in href for word in ['/movies/', '/hindi-', '/download-']):
                    if len(text) > 15: # Movie titles are usually long
                        img = link.find('img')
                        poster = img.get('data-src') or img.get('src') if img else ""

                        if not collection.find_one({"title": text}):
                            collection.insert_one({
                                "title": text,
                                "poster": poster,
                                "source_link": href if href.startswith('http') else target_url.rstrip('/') + href,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"🎬 New Movie: {text}")
                            count += 1
            
            print(f"🏁 Sync Finished. Added {count} movies.")
            
        else:
            print(f"❌ ScraperAPI failed again. Code: {response.status_code}")
            if response.status_code == 403:
                print("💡 Tip: ScraperAPI credits might be low or domain is heavily blacklisted.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
