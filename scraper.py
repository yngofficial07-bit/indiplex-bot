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
        # Premium rendering for full grid load
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&premium=true"
        
        print(f"🚀 Target Site: {target_url}")
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Sirf 'main content' area ko target karo (Header skip karne ke liye)
            content_area = soup.find('main') or soup.find('div', id='content') or soup.find('div', class_='content-area')
            
            if not content_area:
                content_area = soup # Fallback to full page
            
            # 2. Movie items dhoondo (Naya logic)
            # HDHub aksar figure, article ya specific movie-card classes use karta hai
            movie_items = content_area.select('div.rt-movie-card') or \
                          content_area.select('article') or \
                          content_area.select('.post-item')

            # 3. Agar abhi bhi 0 hain, toh images filter karke nikaalo
            if len(movie_items) == 0:
                print("⚠️ Specific cards not found, filtering all images...")
                # Hum un 'a' tags ko dhoondenge jinme movie poster ho sakta hai
                movie_items = [a for a in content_area.find_all('a') if a.find('img')]

            print(f"🔍 Processing {len(movie_items)} potential movies...")

            for item in movie_items:
                try:
                    img_tag = item.find('img')
                    link = item.get('href') if item.name == 'a' else item.find('a')['href']
                    
                    if not img_tag or not link: continue
                    
                    title = img_tag.get('alt') or img_tag.get('title') or ""
                    poster = img_tag.get('data-src') or img_tag.get('src')

                    # --- JORDAR FILTER (Skipping Garbage) ---
                    garbage_keywords = ['logo', 'app', 'telegram', 'banner', 'group', 'join us', 'click here']
                    if any(word in title.lower() for word in garbage_keywords):
                        continue # Inhe ignore karo
                    
                    if len(title) < 5 or not poster: 
                        continue

                    # 4. Save to Database
                    if not collection.find_one({"title": title}):
                        collection.insert_one({
                            "title": title,
                            "poster": poster,
                            "source_link": link,
                            "status": "active",
                            "timestamp": time.time()
                        })
                        print(f"✅ Synced: {title}")
                    else:
                        print(f"⏩ Already exists: {title}")
                except:
                    continue
            
            print(f"🏁 Mission Complete. Database refresh karo!")
        else:
            print(f"❌ ScraperAPI Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Fatal Error: {e}")

if __name__ == "__main__":
    run_scraper()
