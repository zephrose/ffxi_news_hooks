import requests
import xml.etree.ElementTree as ET
import re
import os

WEBHOOK_URL = os.environ['FFXI_DISCORD_WEBHOOK']
RSS_URL = "http://www.playonline.com/pcd/topics/ff11us/topics.xml"
BASE_URL = "http://www.playonline.com"
STATE_FILE = "last_topics_link.txt"

def post_latest_topics():
    response = requests.get(RSS_URL)
    root = ET.fromstring(response.content)
    
    # Namespaces used in FFXI RDF feeds
    ns = {'rss': 'http://purl.org/rss/1.0/', 'dc': 'http://purl.org/dc/elements/1.1/'}

    # Grab the latest item
    item = root.find('.//rss:item', ns)
    title = item.find('rss:title', ns).text
    link = item.find('rss:link', ns).text
    desc_raw = item.find('rss:description', ns).text

    # 1. Extract Image URL if one exists in the CDATA
    img_match = re.search(r'src="([^"]+)"', desc_raw)
    image_url = img_match.group(1) if img_match else None

    # 2. Fix relative links (e.g., /pcd/topics... -> http://playonline.com/pcd/topics...)
    if link.startswith('/'):
        link = BASE_URL + link

    # 3. Clean HTML tags for the text description
    clean_desc = re.sub('<[^<]+?>', '', desc_raw).strip()
    # Remove excessive newlines and "Read on" text
    clean_desc = clean_desc.split("Read on")[0].strip()

    # Read the last link we posted
    last_link = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_link = f.read().strip()

    if link == last_link:
        print("No new articles. Skipping.")
        return

    payload = {
        "embeds": [{
            "title": f"🆕 {title}",
            "url": link,
            "description": clean_desc[:400] + "...", 
            "color": 15105570, # A gold/orange color for Topics
            "image": {"url": image_url} if image_url else None,
            "footer": {"text": "Final Fantasy XI Topics"}
        }]
    }

    requests.post(WEBHOOK_URL, json=payload)

    # Update the state file with the new link
    with open(STATE_FILE, "w") as f:
        f.write(link)

post_latest_topics()