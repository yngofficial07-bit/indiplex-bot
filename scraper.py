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

        target_url = "https://new4.hdhub4u.fo/"
        
        # Premium + Render + Ultra Timeout
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&premium=true&wait_until=networkidle"
        
        print(f"🚀 Hunting movies on: {target_url}")
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Debugging: Page Title check
            print(f"📄 Page Title: {soup.title.string if soup.title else 'No Title'}")

            # Sabse pehle unke standard cards dhoondo
            movies = soup.select('.rt-movie-card') or soup.select('article') or soup.select('.item')
            
            # Agar standard nahi mile, toh har 'a' tag ko dhoondo jisme image ho (The Master Hack)
            if len(movies) == 0:
                print("⚠️ Standard cards not found. Switching to Deep Scan...")
                movies = [a for a in soup.find_all('a') if a.find('img')]

            print(f"🔍 Found {len(movies)} potential items!")

            for movie in movies:
                try:
                    # Link aur Title nikalne ki koshish
                    link = movie.get('href') if movie.name == 'a' else movie.find('a')['href']
                    img_tag = movie.find('img')
                    
                    if not img_tag or not link: continue
                    
                    # Movie sites aksar img ke 'alt' tag mein movie ka naam rakhti hain
                    title = img_tag.get('alt') or img_tag.get('title') or "Untitled Movie"
                    poster = img_tag.get('data-src') or img_tag.get('src')

                    # Sirf wahi links lo jo movie posts ho sakte hain (filter out ads)
                    if "/?p=" in link or "/movies/" in link or len(title) > 5:
                        if not collection.find_one({"title": title}):
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
            
            print(f"🏁 Mission Finished. Database check karo!")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    run_scraper()
