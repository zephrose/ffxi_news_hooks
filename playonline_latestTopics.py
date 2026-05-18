import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = "https://discord.com/api/webhooks/1451447255121793156/UAONMgrw9eVwZqt15YJ028uxXoxvhLqBEF--esECyjOfP5CqP-_KiufkDcf3TcHuu9JQ"#os.environ['FFXI_DISCORD_WEBHOOK']
TOPICS_DATA_URL = "https://www.playonline.com/pcd2/topics/ff11us/topics_latest.html"
HOME_URL = "https://www.playonline.com/ff11us/"
BASE_URL = "http://www.playonline.com"
STATE_FILE = "last_topics_link.txt"

def run():
    # Fetch the raw HTML news fragment directly
    response = requests.get(TOPICS_DATA_URL)
    
    # PlayOnline uses Western encoding
    soup = BeautifulSoup(response.content, "html.parser", from_encoding="latin-1")
    
    # 1. OPTIMIZATION: Target the root-level gutters directly since the parent wrapper is absent
    gutter_blocks = soup.find_all("div", class_="gutter", limit=3)
    
    if not gutter_blocks:
        print("Could not find any 'gutter' blocks in the raw asset data.")
        return
        
    found_topics = []
    
    for block in gutter_blocks:
        # Find the title header (<h4> with class 'tx_topics_tl')
        title_header = block.find("h4", class_="tx_topics_tl")
        if not title_header:
            continue
            
        link_tag = title_header.find("a")
        if not link_tag:
            continue
            
        # Extract raw text and parse out the title vs the date string
        raw_title_text = link_tag.get_text(strip=True)
        
        # Pull out the date (e.g., "05/18/2026") if present in the text
        date_match = re.search(r'\((\d{2}/\d{2}/\d{4})\)', raw_title_text)
        date_str = date_match.group(1) if date_match else None
        
        # Clean up the title by stripping away the trailing date parenthetical
        title = re.sub(r'\s*\(\d{2}/\d{2}/\d{4}\)', '', raw_title_text).strip()
        
        url = link_tag["href"]
        if url.startswith('/'): 
            url = BASE_URL + url
            
        # Find the description paragraph
        desc_tag = block.find("p", class_="tx_topics")
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        
        # Clean up description text (remove trailing links if they duplicate)
        description = description.replace("Read on for details.", "").strip()
        
        # Find the image inside the 'summary-banner' container
        banner_container = block.find("div", class_="summary-banner")
        img_tag = banner_container.find("img") if banner_container else None
        
        image_url = img_tag["src"] if img_tag else None
        if image_url and not image_url.startswith('http'):
            image_url = BASE_URL + image_url

        found_topics.append({
            "title": title,
            "url": url,
            "desc": description[:300] + "..." if len(description) > 300 else description,
            "image": image_url,
            "date": date_str
        })

    # 2. Handle Duplicate Prevention
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            already_posted = f.read().splitlines()
    else:
        already_posted = []

    for topic in found_topics:
        if topic['url'] in already_posted:
            continue

        # Construct a clean layout footer string matching the date
        footer_text = f"FFXI Official Topics • {topic['date']}" if topic['date'] else "FFXI Official Topics"

        payload = {
            "embeds": [{
                "title": f"✨ {topic['title']}",
                "url": topic['url'],
                "description": topic['desc'],
                "color": 15844367, # Gold
                "thumbnail": {"url": topic['image']} if topic['image'] else None,
                "footer": {"text": footer_text}
            }]
        }
        
        requests.post(WEBHOOK_URL, json=payload)
        already_posted.append(topic['url'])

    # 3. Save State
    with open(STATE_FILE, "w") as f:
        f.write("\n".join(already_posted[-20:]))

if __name__ == "__main__":
    run()