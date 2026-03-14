from curl_cffi import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time

MONGO_URI = os.getenv("MONGO_URI")

def run_scraper():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        url = "https://new4.hdhub4u.fo/"
        
        print(f"🕵️ Stealth Mode: Impersonating Chrome to bypass Cloudflare...")
        
        # curl_cffi Chrome ka browser fingerprint copy karega
        response = requests.get(url, impersonate="chrome110", timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Movies dhoondo
            movies = soup.select('div.rt-movie-card') or soup.select('article')
            
            print(f"🔍 Found {len(movies)} movies!")
            
            count = 0
            for movie in movies:
                try:
                    title_tag = movie.find('h3') or movie.find('h2')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag['href']
                        poster = img_tag.get('data-src') or img_tag.get('src') if img_tag else ""

                        if not collection.find_one({"title": title}):
                            collection.insert_one({
                                "title": title,
                                "poster": poster,
                                "source_link": link,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"✅ Synced: {title}")
                            count += 1
                except:
                    continue
            print(f"🏁 Mission Accomplished! Added {count} movies.")
        else:
            print(f"❌ Failed again! Status: {response.status_code}")
            # Agar 403/500 aaye toh header debug karte hain
            print("📄 Response Preview:", response.text[:200])

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
