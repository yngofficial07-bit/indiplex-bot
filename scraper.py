import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time

# Secrets aur API Key
MONGO_URI = os.getenv("MONGO_URI")
SCRAPER_API_KEY = "d1688c53992a7ff781b6e6de27a23f98" # Teri ScraperAPI Key

def run_scraper():
    try:
        # MongoDB Connection
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        # Target URL (HDHub ka latest domain)
        target_url = "https://new4.hdhub4u.fo/"
        
        # ScraperAPI Proxy URL
        # render=true isliye taaki agar JavaScript loading ho toh wo bhi handle ho jaye
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
        
        print(f"🚀 Launching Unstoppable Scraper for: {target_url}")
        
        # Request via ScraperAPI
        response = requests.get(proxy_url, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ ScraperAPI failed with status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Movie Cards find karna
        movies = soup.find_all('div', class_='rt-movie-card') or soup.find_all('article')
        
        print(f"🔍 Found {len(movies)} movies behind Cloudflare!")
        
        for movie in movies:
            try:
                title_tag = movie.find('h3') or movie.find('h2')
                if not title_tag: continue
                title = title_tag.text.strip()
                
                link_tag = movie.find('a')
                img_tag = movie.find('img')
                
                if not link_tag or not img_tag: continue
                
                link = link_tag['href']
                poster = img_tag.get('data-src') or img_tag.get('src')

                print(f"🎬 Syncing: {title}")
                
                # Duplicate check aur Insert
                if not collection.find_one({"title": title}):
                    collection.insert_one({
                        "title": title,
                        "poster": poster,
                        "source_link": link,
                        "status": "active",
                        "timestamp": time.time()
                    })
                    print(f"✅ Database Updated: {title}")
                else:
                    print(f"⏩ Already in Database: {title}")
                    
            except Exception as e:
                print(f"⚠️ Item Error: {e}")

        print("🏁 Mission Successful: Cloudflare Bypassed!")

    except Exception as e:
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    run_scraper()
