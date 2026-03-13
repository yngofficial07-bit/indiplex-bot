import cloudscraper
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os

# GitHub Secrets se URI uthana
MONGO_URI = os.getenv("MONGO_URI")

def run_scraper():
    try:
        # MongoDB Connection
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        # Scraper Setup
        scraper = cloudscraper.create_scraper()
        
        # NAYA DOMAIN YAHAN HAI:
        url = "https://new4.hdhub4u.fo/" 
        
        print(f"🚀 Scraper started for: {url}")
        
        # Request with timeout
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Website access failed! Status Code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HDHub4U ke movie cards find karna (Selector updated)
        # Unke naye design mein aksar 'article' ya specific classes use hote hain
        movies = soup.find_all('div', class_='rt-movie-card') or soup.find_all('article')
        
        print(f"🔍 Found {len(movies)} movies on the page.")
        
        for movie in movies:
            try:
                # Title, Poster aur Link nikalna
                title_tag = movie.find('h3') or movie.find('h2')
                if not title_tag: continue
                
                title = title_tag.text.strip()
                img_tag = movie.find('img')
                link_tag = movie.find('a')
                
                if not img_tag or not link_tag: continue
                
                poster = img_tag.get('src') or img_tag.get('data-src')
                link = link_tag['href']
                
                print(f"🎬 Checking Movie: {title}")
                
                # Database mein duplicate check
                if not collection.find_one({"title": title}):
                    collection.insert_one({
                        "title": title,
                        "poster": poster,
                        "source_link": link,
                        "status": "active"
                    })
                    print(f"✅ Synced to MongoDB: {title}")
                else:
                    print(f"⏩ Already exists: {title}")
                    
            except Exception as item_error:
                print(f"⚠️ Item Error: {item_error}")

        print("🏁 Mission Accomplished!")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    run_scraper()
