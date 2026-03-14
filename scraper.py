from curl_cffi import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time
import random

MONGO_URI = os.getenv("MONGO_URI")

def get_free_proxies():
    try:
        url = "https://free-proxy-list.net/"
        res = requests.get(url, impersonate="chrome110")
        soup = BeautifulSoup(res.text, 'html.parser')
        proxies = []
        for row in soup.select("table.table-striped tbody tr"):
            cols = row.find_all("td")
            if cols[4].text == "elite proxy" and cols[6].text == "yes": # HTTPS & Elite
                proxies.append(f"http://{cols[0].text}:{cols[1].text}")
        return proxies
    except:
        return []

def run_scraper():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        target_url = "https://new4.hdhub4u.fo/"
        proxies = get_free_proxies()
        
        print(f"📡 Found {len(proxies)} fresh proxies. Starting bypass attempt...")

        success = False
        for proxy in proxies[:10]: # Top 10 proxies try karenge
            try:
                print(f"🔄 Trying Proxy: {proxy}")
                # Stealth request with Proxy
                response = requests.get(
                    target_url, 
                    impersonate="chrome110", 
                    proxies={"http": proxy, "https": proxy},
                    timeout=20
                )
                
                if response.status_code == 200 and "Just a moment" not in response.text:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    movies = soup.select('div.rt-movie-card') or soup.select('article')
                    
                    if len(movies) > 0:
                        print(f"🎯 BINGO! Found {len(movies)} movies using proxy {proxy}")
                        for movie in movies:
                            # ... (Same parsing logic as before) ...
                            title_tag = movie.find('h3') or movie.find('h2')
                            link_tag = movie.find('a')
                            img_tag = movie.find('img')
                            if title_tag and link_tag:
                                title = title_tag.get_text(strip=True)
                                if not collection.find_one({"title": title}):
                                    collection.insert_one({
                                        "title": title,
                                        "poster": img_tag.get('data-src') or img_tag.get('src') if img_tag else "",
                                        "source_link": link_tag['href'],
                                        "status": "active",
                                        "timestamp": time.time()
                                    })
                                    print(f"✅ Saved: {title}")
                        success = True
                        break
            except Exception as e:
                print(f"❌ Proxy {proxy} failed.")
                continue

        if not success:
            print("💀 All bypass attempts failed. Cloudflare is winning today.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    run_scraper()
