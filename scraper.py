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
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true"
        
        print(f"🚀 Scraping with Wide-Selectors: {target_url}")
        response = requests.get(proxy_url, timeout=90)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # AGGRESSIVE SELECTORS: Sab kuch check karo
            movies = soup.select('.rt-movie-card') or soup.select('article') or soup.select('.item') or soup.select('.post')
            
            print(f"🔍 Found {len(movies)} potential movies!")
            
            for movie in movies:
                try:
                    # Generic search for Title, Link and Poster
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')
                    title_tag = movie.find('h3') or movie.find('h2') or (link_tag.get('title') if link_tag else None)

                    if link_tag and img_tag:
                        title = title_tag.text.strip() if hasattr(title_tag, 'text') else str(title_tag)
                        link = link_tag['href']
                        poster = img_tag.get('data-src') or img_tag.get('src')

                        if title and not collection.find_one({"title": title}):
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
            print("🏁 Process Finished!")
        else:
            print(f"💀 API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
