import json
import os
import requests

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
payload_path = os.path.join(project_root, "backend", "app", "live_news_payload.json")

with open(payload_path, "r", encoding="utf-8") as f:
    data = json.load(f)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"=== STORED PAYLOAD FILE: {payload_path} ===")
print(f"=== TICKER: {data.get('ticker')} | TOTAL ARTICLES: {len(data.get('articles', []))} ===\n")

for idx, a in enumerate(data.get("articles", []), 1):
    rss_url = a["url"]
    try:
        r = requests.get(rss_url, headers=headers, allow_redirects=True, timeout=5)
        direct_url = r.url if r.url else rss_url
    except Exception:
        direct_url = rss_url
        
    a["direct_url"] = direct_url
    print(f"{idx:2d}. Headline: {a['headline']}")
    print(f"    Source  : {a['source']}")
    print(f"    Date    : {a['published_date']}")
    print(f"    Link    : {direct_url}")
    print(f"    RSS Link: {rss_url}\n")

# Save updated payload with direct_url field
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
