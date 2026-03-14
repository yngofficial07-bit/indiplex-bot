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

        # Hum seedha Home Page aur Category dono try karenge
        target_url = "https://new4.hdhub4u.fo/"
        
        print(f"🚀 Discovery Mode ON for: {target_url}")
        
        # ScraperAPI with Premium + Residential (Best for 500 errors)
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true"
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Sabse pehle saare Links nikal lo
            all_links = soup.find_all('a')
            print(f"📊 Total Links on Page: {len(all_links)}")

            # 2. Movie containers dhoondo (Broad Range)
            # Hum har us 'div' ya 'article' ko check karenge jisme 'post', 'movie', ya 'card' likha ho
            items = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['movie', 'post', 'item', 'card']))
            
            print(f"🎬 Potential Movie Containers: {len(items)}")

            # 3. Processing
            count = 0
            for item in (items if items else all_links):
                try:
                    img_tag = item.find('img')
                    link_tag = item if item.name == 'a' else item.find('a')
                    
                    if not img_tag or not link_tag: continue
                    
                    title = img_tag.get('alt') or img_tag.get('title') or "No Title"
                    link = link_tag.get('href')
                    poster = img_tag.get('data-src') or img_tag.get('src')

                    # DEBUG: Sab kuch print karo jo mil raha hai
                    print(f"👀 Found Raw Item: {title[:30]}...")

                    # Filter Garbage
                    if any(x in title.lower() for x in ['logo', 'app', 'telegram', 'join']):
                        continue
                    
                    if len(title) > 5 and poster and "http" in link:
                        if not collection.find_one({"title": title}):
                            collection.insert_one({
                                "title": title,
                                "poster": poster,
                                "source_link": link,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"✅ SYNCED: {title}")
                            count += 1
                        else:
                            print(f"⏩ ALREADY EXISTS: {title}")
                except:
                    continue
            
            print(f"🏁 Mission Finished. Total New Movies Synced: {count}")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
