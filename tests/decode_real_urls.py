import json
import os
from googlenewsdecoder import gnewsdecoder

payload_path = os.path.join("backend", "app", "live_news_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== DECODING GOOGLE NEWS RSS LINKS TO DIRECT PUBLISHER URLS ===\n")

for idx, a in enumerate(data.get("articles", []), 1):
    rss_url = a["url"]
    try:
        decoded = gnewsdecoder(rss_url, interval=1)
        direct_url = decoded.get("decoded_url") if isinstance(decoded, dict) and decoded.get("status") else rss_url
    except Exception as e:
        direct_url = rss_url

    a["url"] = direct_url
    a["rss_url"] = rss_url
    print(f"Article #{idx}: [{a['source']}]")
    print(f"  Title     : {a['headline']}")
    print(f"  Direct Link: {direct_url}\n")

# Save updated direct_url to payload file
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Saved direct publisher links to: {payload_path}")
