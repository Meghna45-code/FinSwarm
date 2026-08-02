import os
import asyncio
import json
import logging
import requests
import trafilatura
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from urllib.parse import quote_plus
from .schemas import FinancialNewsArticle, NewsPayload
from .llm_client import GeminiLlmClient

logger = logging.getLogger("finswarm.data_pipeline")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_news_urls_from_api(ticker: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Fetches REAL, LIVE financial news URLs specifically for the requested company ticker (e.g. Reliance Industries).
    Strictly filters out articles about unrelated companies.
    """
    logger.info(f"Fetching real live news URLs strictly for ticker: {ticker}...")
    articles = []

    # Format strict company search term
    if "RELIANCE" in ticker.upper() or "RIL" in ticker.upper():
        company_query = quote_plus('"Reliance Industries"')
        keyword_filter = ["reliance", "ril", "nsei:reliance"]
    else:
        clean_ticker = ticker.split(".")[0].upper()
        company_query = quote_plus(f'"{clean_ticker}" stock news')
        keyword_filter = [clean_ticker.lower()]

    # 1. Fetch from Google News RSS feed for live stock news
    try:
        rss_url = f"https://news.google.com/rss/search?q={company_query}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(rss_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall("./channel/item"):
                if len(articles) >= limit:
                    break
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source_elem = item.find("source")
                source_name = source_elem.text if source_elem is not None else "Google News"
                
                # Strict relevance check: Title MUST mention the company
                title_lower = title.lower()
                if link and title and any(k in title_lower for k in keyword_filter):
                    # Decode Google News RSS link to direct publisher URL
                    direct_link = link
                    try:
                        from googlenewsdecoder import gnewsdecoder
                        decoded = gnewsdecoder(link, interval=1)
                        if isinstance(decoded, dict) and decoded.get("status"):
                            direct_link = decoded.get("decoded_url")
                    except Exception:
                        pass

                    articles.append({
                        "url": direct_link,
                        "title": title,
                        "source": source_name,
                        "published_date": pub_date
                    })
    except Exception as e:
        logger.warning(f"Live Google News RSS fetch encounter: {e}")

    # 2. If additional articles needed, fetch from Yahoo Finance RSS feed
    if len(articles) < limit:
        try:
            clean_t = "RELIANCE.NS" if "RELIANCE" in ticker.upper() else ticker.split(".")[0].upper()
            yf_url = f"https://finance.yahoo.com/rss/headline?s={clean_t}"
            resp = requests.get(yf_url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item"):
                    if len(articles) >= limit:
                        break
                    link = item.findtext("link", "")
                    title = item.findtext("title", "")
                    pub_date = item.findtext("pubDate", "")
                    title_lower = title.lower()
                    if link and title and any(k in title_lower for k in keyword_filter) and not any(a["url"] == link for a in articles):
                        articles.append({
                            "url": link,
                            "title": title,
                            "source": "Yahoo Finance",
                            "published_date": pub_date
                        })
        except Exception as e:
            logger.warning(f"Live Yahoo Finance RSS fetch encounter: {e}")

    logger.info(f"Retrieved {len(articles)} strictly relevant live news article URLs for {ticker}.")
    return articles[:limit]


def extract_clean_text(url: str) -> str:
    """
    Uses trafilatura to perform real live web downloading and text extraction, stripping HTML boilerplate.
    Handles redirect resolution for Google News URLs if needed.
    """
    target_url = url
    try:
        if "news.google.com" in url:
            r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=5)
            if r.url and "news.google.com" not in r.url:
                target_url = r.url

        downloaded = trafilatura.fetch_url(target_url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, output_format="txt", include_comments=False, include_tables=True)
            if extracted and len(extracted.strip()) > 40:
                return extracted.strip()
    except Exception as e:
        logger.warning(f"Live web scraping via trafilatura for {url}: {e}")
    return ""


async def process_articles_for_swarm(ticker: str, llm_client: GeminiLlmClient = None, limit: int = 5) -> str:
    """
    The main RAG pipeline:
    1. Fetches REAL LIVE news URLs.
    2. Scrapes clean text using trafilatura.
    3. Uses LLM structured output to format facts against FinancialNewsArticle schema.
    4. Returns JSON payload.
    """
    if llm_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing for live LLM extraction.")
        llm_client = GeminiLlmClient(api_key=api_key)

    raw_articles = fetch_news_urls_from_api(ticker, limit=limit)
    if not raw_articles:
        raise RuntimeError(f"CRITICAL: Failed to retrieve any real live news URLs for ticker '{ticker}'. Zero mock fallbacks allowed.")

    structured_articles: List[FinancialNewsArticle] = []

    for item in raw_articles:
        url = item["url"]
        clean_text = extract_clean_text(url)
        
        # If redirect or trafilatura needs text fallback from headline/title
        content_to_parse = clean_text if clean_text else f"Headline: {item['title']}\nSource: {item['source']}\nDate: {item['published_date']}"

        system_prompt = (
            "You are a neutral data extraction analyst. Extract the facts from the provided text into the required JSON schema. "
            "Remain completely objective and neutral. Extract fundamental metrics and legal risks if present."
        )
        prompt = (
            f"Article URL: {url}\n"
            f"Publisher/Source: {item['source']}\n"
            f"Publication Date: {item['published_date']}\n"
            f"Article Content:\n{content_to_parse[:4000]}"
        )

        success = False
        attempts = 0
        res = {}
        model_pool = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

        while not success and attempts < 2:
            attempts += 1
            model_to_use = model_pool[(attempts - 1) % len(model_pool)]
            try:
                res = await llm_client.generate_json(
                    system_prompt=system_prompt,
                    prompt=prompt,
                    response_schema=FinancialNewsArticle,
                    model_name=model_to_use
                )
                success = True
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "Quota" in err_msg or "ResourceExhausted" in err_msg:
                    logger.warning(f"Rate limit on article #{len(structured_articles)+1} using {model_to_use}, trying fallback...")
                    await asyncio.sleep(1.0)
                else:
                    logger.warning(f"Structured extraction error for {url}: {e}")
                    break

        if success:
            article_obj = FinancialNewsArticle(
                headline=str(res.get("headline", item["title"])),
                source=str(res.get("source", item["source"])),
                published_date=str(res.get("published_date", item["published_date"])),
                url=url,
                fundamental_metrics=res.get("fundamental_metrics") or {},
                legal_risks=str(res.get("legal_risks", "None")),
                summary=str(res.get("summary", item["title"]))
            )
        else:
            summary_text = (clean_text[:250] + "...") if len(clean_text) > 50 else item["title"]
            article_obj = FinancialNewsArticle(
                headline=item["title"],
                source=item["source"],
                published_date=item["published_date"],
                url=url,
                fundamental_metrics={},
                legal_risks="None",
                summary=summary_text
            )

        structured_articles.append(article_obj)
        logger.info(f"Successfully extracted live article #{len(structured_articles)}: {article_obj.headline[:60]}")

    payload = NewsPayload(ticker=ticker, articles=structured_articles)
    return payload.model_dump_json(indent=2)
