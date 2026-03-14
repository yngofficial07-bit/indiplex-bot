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

        # Vegamovies Target
        target_url = "https://vegamovies.actor/" 
        
        # ScraperAPI with Premium (Bypass for stable connection)
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true"
        
        print(f"🚀 Switching target to: {target_url}")
        
        response = requests.get(proxy_url, timeout=60)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Vegamovies movie container detection
            # Ye 'article' ya 'div' mein cards rakhte hain
            movies = soup.find_all('article') or soup.find_all('div', class_='blog-post')
            
            print(f"📡 Found {len(movies)} potential movies.")
            
            count = 0
            for movie in movies:
                try:
                    # Title aur Link extraction
                    title_tag = movie.find('h3') or movie.find('h2')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag['href']
                        # Poster image (handles lazy loading)
                        poster = img_tag.get('data-src') or img_tag.get('src') or ""

                        # Database insertion
                        if not collection.find_one({"title": title}):
                            collection.insert_one({
                                "title": title,
                                "poster": poster,
                                "source_link": link,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"🎬 Synced: {title}")
                            count += 1
                        else:
                            print(f"⏩ Existing: {title}")
                except Exception as e:
                    continue
            
            print(f"🏁 Done! Total new movies added: {count}")
        else:
            print(f"❌ ScraperAPI Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
