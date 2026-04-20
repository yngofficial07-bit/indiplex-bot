import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi
import os
import time
import json

MONGO_URI = os.getenv("MONGO_URI")
SCRAPER_API_KEY = "d1688c53992a7ff781b6e6de27a23f98"

def run_scraper():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client["indiplex_db"]
        collection = db["media_vault"]

        # Vegamovies Target (Success Rate High Hai)
        target_url = "https://vegamovise2.com.in/" 
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&premium=true"
        
        print(f"🚀 Scraping started for: {target_url}")
        response = requests.get(proxy_url, timeout=60)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            movies = soup.find_all('article') or soup.find_all('div', class_='blog-post')
            
            movie_list = []
            for movie in movies:
                try:
                    title_tag = movie.find('h3') or movie.find('h2')
                    link_tag = movie.find('a')
                    img_tag = movie.find('img')

                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag['href']
                        poster = img_tag.get('data-src') or img_tag.get('src') or ""
                        
                        # Poster path fix (Domain jodna)
                        if poster.startswith('/'):
                            poster = "https://vegamovise2.com.in" + poster

                        data = {"title": title, "poster": poster, "link": link}
                        
                        # 1. MongoDB mein save
                        if not collection.find_one({"title": title}):
                            collection.insert_one(data)
                        
                        # 2. Local list mein add (JSON ke liye)
                        movie_list.append(data)
                except: continue

            # movies.json file create karna
            with open('movies.json', 'w') as f:
                json.dump(movie_list, f, indent=4)
            
            print(f"✅ Mission Success! {len(movie_list)} movies saved to movies.json")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_scraper()
