import asyncio
import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from backend.app.services.data_pipeline import process_articles_for_swarm, fetch_news_urls_from_api

async def main():
    ticker = "RELIANCE.NS"
    print(f"=========================================================================")
    print(f"   FINSWARM RAG PIPELINE: FETCHING & EXTRACTING 10 REAL LIVE NEWS HEADLINES")
    print(f"=========================================================================\n")
    
    # 1. Fetch 10 real live news article metadata & URLs
    raw_urls = fetch_news_urls_from_api(ticker, limit=10)
    print(f"Discovered {len(raw_urls)} REAL LIVE article URLs from Google & Yahoo Finance feeds:")
    for idx, item in enumerate(raw_urls, 1):
        print(f"  {idx:2d}. [{item['source']}] {item['title']}")
        print(f"      URL: {item['url']}")

    # 2. Process with live trafilatura extraction & Gemini structured JSON output
    print(f"\nExecuting live trafilatura extraction and Gemini structured schema parsing...")
    json_output_str = await process_articles_for_swarm(ticker=ticker, limit=10)
    
    output_file = os.path.join(project_root, "backend", "app", "live_news_payload.json")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(json_output_str)

    print(f"\nSuccessfully generated and saved 10 live news payload to: {output_file}\n")
    print("=== EXTRACTED 10 LIVE NEWS PAYLOAD (Pydantic NewsPayload JSON) ===")
    print(json_output_str)

if __name__ == "__main__":
    asyncio.run(main())
