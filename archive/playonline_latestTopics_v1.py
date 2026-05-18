import requests
from bs4 import BeautifulSoup
import os
import re

WEBHOOK_URL = os.environ['FFXI_DISCORD_WEBHOOK']
HOME_URL = "http://www.playonline.com/ff11us/index.shtml"
BASE_URL = "http://www.playonline.com"
STATE_FILE = "last_topics_link.txt"

def run():
    response = requests.get(HOME_URL)
    # PlayOnline often uses Western encoding
    soup = BeautifulSoup(response.content, "html.parser", from_encoding="latin-1")
    
    # 1. Locate the Topic Headline section
    hg_header = soup.find("p", class_="tx_topics_hg4")
    if not hg_header:
        print("Could not find the topics header class.")
        return

    found_topics = []
    # 2. Iterate through siblings following the header
    # We look for tx_topics_tl for the title/link and the next tx_topics for description
    current = hg_header.find_next_sibling()
    
    while current and len(found_topics) < 3:
        if "tx_topics_tl" in current.get("class", []):
            link_tag = current.find("a")
            if link_tag:
                title = link_tag.get_text(strip=True)
                url = link_tag["href"]
                if url.startswith('/'): url = BASE_URL + url
                
                # The description is usually the very next sibling with class 'tx_topics'
                desc_tag = current.find_next_sibling("p", class_="tx_topics")
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                
                # Look for an image inside that description tag
                img_tag = desc_tag.find("img") if desc_tag else None
                image_url = img_tag["src"] if img_tag else None
                if image_url and not image_url.startswith('http'):
                    image_url = BASE_URL + image_url

                found_topics.append({
                    "title": title,
                    "url": url,
                    "desc": description[:400] + "..." if len(description) > 400 else description,
                    "image": image_url
                })
        current = current.find_next_sibling()

    # 3. Handle Duplicate Prevention
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            already_posted = f.read().splitlines()
    else:
        already_posted = []

    for topic in found_topics:
        if topic['url'] in already_posted:
            continue

        payload = {
            "embeds": [{
                "title": f"✨ {topic['title']}",
                "url": topic['url'],
                "description": topic['desc'],
                "color": 15844367, # Gold
                "image": {"url": topic['image']} if topic['image'] else None,
                "footer": {"text": "FFXI Official Topics"}
            }]
        }
        
        requests.post(WEBHOOK_URL, json=payload)
        already_posted.append(topic['url'])

    # 4. Save State
    with open(STATE_FILE, "w") as f:
        f.write("\n".join(already_posted[-20:]))

if __name__ == "__main__":
    run()