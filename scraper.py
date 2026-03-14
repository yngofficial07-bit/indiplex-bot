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
        
        # Premium settings for guaranteed bypass
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true&country_code=us"
        
        print(f"🚀 Hunting movies on: {target_url}")
        
        response = requests.get(proxy_url, timeout=90)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # BROAD SELECTORS: Hum un sabhi divs ko dhoondenge jo movie card ho sakte hain
            # HDHub aksar 'article', 'li' ya specific classes use karta hai
            movies = soup.find_all('div', class_='rt-movie-card') or \
                     soup.find_all('article') or \
                     soup.select('.post-item') or \
                     soup.select('.ml-item')

            print(f"🔍 Found {len(movies)} potential containers.")
            
            count = 0
            for movie in movies:
                try:
                    # Title nikalne ke multiple tarike
                    title_tag = movie.find('h3') or movie.find('h2') or movie.find('font')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag['href']
                        # Poster check (data-src, lazy-src, etc.)
                        poster = ""
                        if img_tag:
                            poster = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-lazy-src')

                        # Clean up link agar relative hai
                        if link.startswith('/'):
                            link = "https://new4.hdhub4u.fo" + link

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
                except Exception:
                    continue
            
            print(f"🏁 Done! Total new movies added: {count}")
        else:
            print(f"❌ ScraperAPI Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
