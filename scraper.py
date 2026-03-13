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
        url = "https://hdhub4u.actor/" # Latest domain
        
        print(f"🚀 Scraper started for: {url}")
        
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"❌ Website access failed! Status Code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HDHub4U ke movie cards find karna
        # Note: Agar selector change hua hoga toh humein logs mein '0 movies' dikhega
        movies = soup.find_all('div', class_='rt-movie-card') 
        
        print(f"🔍 Found {len(movies)} movies on the page.")
        
        for movie in movies:
            try:
                title_tag = movie.find('h3')
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                poster = movie.find('img')['src']
                link = movie.find('a')['href']
                
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
                    print(f"⏩ Already exists, skipping: {title}")
                    
            except Exception as item_error:
                print(f"⚠️ Error processing a movie item: {item_error}")

        print("🏁 Scraper finished execution successfully!")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    run_scraper()
