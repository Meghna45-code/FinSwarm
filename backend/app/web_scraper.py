import logging
import re

logger = logging.getLogger("finswarm.web_scraper")

async def scrape_url(url: str) -> str:
    """
    Asynchronously fetches a URL and extracts the core text content, 
    stripping out HTML, scripts, styles, and standard navigation elements.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        # Using a standard user-agent prevents basic bot-blocking from news sites
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=15.0)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Destroy elements that contain non-article text
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            element.extract()
            
        # Get text and condense excessive whitespace
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return f"Notice: Successfully reached {url}, but could not extract readable text."
            
        logger.info(f"Successfully scraped URL: {url}")
        return text
        
    except ImportError:
        logger.error("Web scraping dependencies missing.")
        return "Error: httpx and beautifulsoup4 are not installed. Run `pip install httpx beautifulsoup4`."
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error scraping URL {url}: {e}")
        return f"Error: Unable to fetch the website. It may be blocking scrapers. ({str(e)})"
    except Exception as e:
        logger.exception(f"Web Scraping Error for {url}: {e}")
        return f"Error processing URL: {str(e)}"