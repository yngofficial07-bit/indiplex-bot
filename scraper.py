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

        # Hum .fo ki jagah unka alternative try karte hain jo aksar kam secure hota hai
        target_url = "https://hdhub4u.monster/" 
        
        # render=true zaroori ho sakta hai agar content JS se aa raha ho
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
        
        print(f"🚀 Debugging HTML on: {target_url}")
        
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # SABSE SIMPLE SELECTOR: Sirf 'a' tags (links) dhoondo jinke andar movie titles ho sakte hain
            links = soup.find_all('a')
            print(f"📡 Total links found on page: {len(links)}")
            
            count = 0
            for link_tag in links:
                href = link_tag.get('href', '')
                # HDHub ke movie links mein aksar ye words hote hain
                if '/movies/' in href or '/hindi-dubbed/' in href or '/bollywood-movies/' in href:
                    title = link_tag.get_text(strip=True)
                    
                    if len(title) > 10: # Chhote links ko skip karo
                        # Poster dhoondne ke liye link ke andar ki image dekho
                        img_tag = link_tag.find('img')
                        poster = ""
                        if img_tag:
                            poster = img_tag.get('data-src') or img_tag.get('src')

                        if not collection.find_one({"title": title}):
                            collection.insert_one({
                                "title": title,
                                "poster": poster,
                                "source_link": href if href.startswith('http') else target_url + href,
                                "status": "active",
                                "timestamp": time.time()
                            })
                            print(f"✅ Found & Synced: {title}")
                            count += 1
            
            if count == 0:
                print("⚠️ Still 0 movies. Checking if page is blocked or empty...")
                # Debugging ke liye HTML ka chhota hissa print karo
                print("HTML Snippet:", response.text[:500]) 

            print(f"🏁 Processed. Added: {count}")
        else:
            print(f"❌ Error Code: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
