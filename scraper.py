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

        # RSS FEED: Ye seedha latest posts ka XML data nikalta hai
        # Sabse safe aur sabse fast tarika
        target_url = "https://new4.hdhub4u.fo/feed/"
        
        print(f"📡 Accessing Secret RSS Feed: {target_url}")
        
        # Premium mode to bypass Cloudflare on Feed
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true"
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            # RSS XML format mein hota hai
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            print(f"📦 Found {len(items)} latest movie posts in Feed!")

            count = 0
            for item in items:
                try:
                    title = item.title.text.strip()
                    link = item.link.text.strip()
                    
                    # Image nikalne ke liye description mein jhaankna padta hai
                    description = item.description.text if item.description else ""
                    desc_soup = BeautifulSoup(description, 'html.parser')
                    img_tag = desc_soup.find('img')
                    
                    poster = ""
                    if img_tag:
                        poster = img_tag.get('src') or img_tag.get('data-src')

                    # Agar image nahi mili, toh hum default poster ya scraper se nikalenge
                    if not poster:
                        poster = "https://via.placeholder.com/300x450?text=Poster+Pending"

                    # Database Sync
                    if not collection.find_one({"title": title}):
                        collection.insert_one({
                            "title": title,
                            "poster": poster,
                            "source_link": link,
                            "status": "active",
                            "timestamp": time.time()
                        })
                        print(f"✅ RSS SYNCED: {title}")
                        count += 1
                    else:
                        print(f"⏩ Already Synced: {title[:20]}...")
                except Exception as e:
                    print(f"⚠️ Item Error: {e}")
                    continue
            
            print(f"🏁 RSS Mission Finished! Total Added: {count}")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
