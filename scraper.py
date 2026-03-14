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
        
        # Advanced Proxy URL (Adding ultra-premium settings)
        # premium=true Cloudflare bypass ke liye best hai
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true&country_code=us"
        
        print(f"🚀 Final Boss Scraper starting for: {target_url}")
        
        response = requests.get(proxy_url, timeout=90) # Extra timeout for premium
        
        if response.status_code != 200:
            print(f"❌ ScraperAPI Status: {response.status_code}. Checking backup mirror...")
            # Agar primary fail ho, toh Mirror site try karo bina premium ke
            target_url = "https://hdhub4u.mx/"
            proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
            response = requests.get(proxy_url, timeout=60)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # HDHub ke common classes
            movies = soup.find_all('div', class_='rt-movie-card') or soup.select('article')
            
            print(f"🔍 Found {len(movies)} movies!")
            
            for movie in movies:
                try:
                    title_tag = movie.find('h3') or movie.find('h2')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.text.strip()
                        link = link_tag['href']
                        # Poster image dhoondne ka logic
                        poster = ""
                        if img_tag:
                            poster = img_tag.get('data-src') or img_tag.get('src') or ""

                        if not collection.find_one({"title": title}):
                            collection.insert_one({
                                "title": title,
                                "poster": poster,
                                "source_link": link,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"✅ Sync Successful: {title}")
                except Exception as e:
                    continue
            print("🏁 Sync Complete!")
        else:
            print(f"💀 Still getting {response.status_code}. Bhai, domain block ho gaya lagta hai.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
