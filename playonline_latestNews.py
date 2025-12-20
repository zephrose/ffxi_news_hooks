import requests
import xml.etree.ElementTree as ET
import re
import os

# Your Webhook URL
RSS_URL = "http://www.playonline.com/ff11us/polnews/news.xml"
WEBHOOK_URL = "https://discord.com/api/webhooks/1451447255121793156/UAONMgrw9eVwZqt15YJ028uxXoxvhLqBEF--esECyjOfP5CqP-_KiufkDcf3TcHuu9JQ"
STATE_FILE = "last_news_link.txt"

def post_latest_news():
    response = requests.get(RSS_URL)
    root = ET.fromstring(response.content)

    # Namespace handling for FFXI's RDF format
    ns = {'rss': 'http://purl.org/rss/1.0/', 'dc': 'http://purl.org/dc/elements/1.1/'}

    # Get the latest item
    item = root.find('.//rss:item', ns)
    title = item.find('rss:title', ns).text
    link = item.find('rss:link', ns).text
    desc_raw = item.find('rss:description', ns).text

    # Clean up HTML tags from the description
    clean_desc = re.sub('<[^<]+?>', '', desc_raw).strip()

    # Read the last link we posted
    last_link = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_link = f.read().strip()

    if link == last_link:
        print("No new articles. Skipping.")
        return

    # Create the Embed JSON
    payload = {
        "embeds": [{
            "title": title,
            "url": link,
            "description": clean_desc[:500] + "...", # Truncate if too long
            "color": 25500, # A nice FFXI Blue
            "footer": {"text": "FFXI Official News"}
        }]
    }

    requests.post(WEBHOOK_URL, json=payload)

    # Update the state file with the new link
    with open(STATE_FILE, "w") as f:
        f.write(link)


post_latest_news()