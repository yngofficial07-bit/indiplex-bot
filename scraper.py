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

        # Target URL
        target_url = "https://new4.hdhub4u.fo/"
        
        # ScraperAPI Lite URL (Removing render=true to avoid 500 error)
        # Adding country_code=us for better success rate
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&country_code=us"
        
        print(f"🚀 Re-attempting with ScraperAPI Lite: {target_url}")
        
        response = requests.get(proxy_url, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ ScraperAPI Status: {response.status_code}. Trying direct mirror...")
            # Agar phir bhi fail ho, toh backup mirror try karo
            target_url = "https://hdhub4u.lat/"
            proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
            response = requests.get(proxy_url, timeout=60)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Selectors ko thoda wide rakhte hain
            movies = soup.select('div.rt-movie-card') or soup.select('article')
            
            print(f"🔍 Found {len(movies)} movies!")
            
            for movie in movies:
                try:
                    title_tag = movie.find('h3') or movie.find('h2')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.text.strip()
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
                except Exception as e:
                    continue
        else:
            print(f"💀 Still failing with status {response.status_code}. HDHub might be down or heavily shielded.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    run_scraper()
