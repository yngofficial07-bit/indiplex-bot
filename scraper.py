import cloudscraper
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time

# GitHub Secrets se URI uthana
MONGO_URI = os.getenv("MONGO_URI")

def run_scraper():
    try:
        # MongoDB Connection
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        # Cloudscraper Setup with Browser Emulation (To bypass 403)
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Naya Domain
        url = "https://new4.hdhub4u.fo/" 
        
        print(f"🚀 Attempting to scrape: {url}")
        
        # Requesting the page
        response = scraper.get(url, timeout=30)
        
        if response.status_code == 403:
            print("❌ Access Denied (403): Cloudflare is still blocking. Trying alternative...")
            # Agar 403 aata hai toh ek mirror site try karte hain
            url = "https://hdhub4u.lat/"
            response = scraper.get(url, timeout=30)

        if response.status_code != 200:
            print(f"❌ Failed! Status Code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HDHub4U ke naye design ke hisaab se selectors
        # Hum multiple options check karenge
        movies = soup.find_all('div', class_='rt-movie-card') or soup.find_all('article')
        
        print(f"🔍 Found {len(movies)} movie containers.")
        
        for movie in movies:
            try:
                # Title dhundna
                title_tag = movie.find('h3') or movie.find('h2')
                if not title_tag: continue
                title = title_tag.text.strip()
                
                # Link dhundna
                link_tag = movie.find('a')
                if not link_tag: continue
                link = link_tag['href']
                
                # Image/Poster dhundna (data-src handle karne ke liye)
                img_tag = movie.find('img')
                if not img_tag: continue
                poster = img_tag.get('data-src') or img_tag.get('src')

                print(f"🎬 Processing: {title}")
                
                # Duplicate check aur Insert
                if not collection.find_one({"title": title}):
                    collection.insert_one({
                        "title": title,
                        "poster": poster,
                        "source_link": link,
                        "status": "active",
                        "created_at": time.time()
                    })
                    print(f"✅ Saved to Database: {title}")
                else:
                    print(f"⏩ Skipping (Duplicate): {title}")
                    
            except Exception as item_error:
                print(f"⚠️ Item-level Error: {item_error}")

        print("🏁 Mission Successful!")

    except Exception as e:
        print(f"❌ Critical System Error: {e}")

if __name__ == "__main__":
    run_scraper()
