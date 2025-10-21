import os, time, logging, random
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import feedparser
from playwright.sync_api import sync_playwright

# scrappes un site pour y récupérer les données dont on a besoin

def sleep_jitter(min_s=0.8, max_s=1.8):
    """Pause aléatoire pour éviter les rafales suspectes."""
    time.sleep(random.uniform(min_s, max_s))
    
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

# Config
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}
TIMEOUT = 15
RATE_SLEEP = 1.2  # pause entre requêtes
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXIES = None
if USE_PROXY:
    user = os.getenv("BRD_USERNAME")
    pwd  = os.getenv("BRD_PASSWORD")
    host = os.getenv("BRD_HOST", "brd.superproxy.io")
    port = os.getenv("BRD_PORT", "22225")
    proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    PROXIES = {"http": proxy_url, "https": proxy_url}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def try_rss(url):
    """Retourne list d'items (title, link, published) si RSS ok, sinon []"""
    feed_url = url.rstrip("/") + "/feed"
    logging.info("Try RSS: %s", feed_url)
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            return []
        items = []
        for e in feed.entries:
            items.append({
                "title": e.get("title"),
                "url": e.get("link"),
                "date": e.get("published") or e.get("updated")
            })
        return items
    except Exception as e:
        logging.warning("RSS failed: %s", e)
        return []

def try_requests(url):
    """Requête simple + parse HTML. Retourne raw html ou None si bloqué."""
    logging.info("Try requests GET: %s", url)
    try:
        sleep_jitter() #anti rafale
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
        r.raise_for_status()
        text = r.text
        # très simple check Cloudflare block
        if "Attention Required" in text or "Please enable cookies" in text or "Sorry, you have been blocked" in text:
            logging.warning("Blocked by Cloudflare or similar.")
            return None
        return text
    except Exception as e:
        logging.warning("Requests failed: %s", e)
        return None

def try_playwright(url):
    """Fallback: render page with Playwright (si installé). Retourne HTML ou None."""
    if not PLAYWRIGHT_AVAILABLE:
        logging.warning("Playwright not available.")
        return None
    logging.info("Try Playwright: %s", url)
    try:
        with sync_playwright() as p:
            sleep_jitter()
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=HEADERS["User-Agent"])
            page = ctx.new_page()
            page.goto(url, timeout=60000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logging.warning("Playwright failed: %s", e)
        return None

def extract_list_from_html(html, base=None):
    """EXEMPLE simple: récupérer liens d'articles depuis <li> article a[href]"""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("li article a[href]"):
        href = a.get("href")
        if not href:
            continue
        link = href if href.startswith("http") else urljoin(base or "", href)
        title = a.get_text(strip=True) or a.get("title") or ""
        out.append({"title": title, "url": link})
    return out

def fetch_source(url):
    """Flow: rss -> requests -> playwright. Retourne liste d'items (title,url,maybe date)."""
    # 1) RSS
    rss_items = try_rss(url)
    if rss_items:
        logging.info("RSS success, %d items", len(rss_items))
        return rss_items

    # 2) requests
    html = try_requests(url)
    if html:
        items = extract_list_from_html(html, base=url)
        if items:
            logging.info("Requests parse ok, %d items", len(items))
            return items

    # 3) playwright
    html = try_playwright(url)
    if html:
        items = extract_list_from_html(html, base=url)
        logging.info("Playwright parse ok, %d items", len(items))
        return items

    logging.error("All methods failed for %s", url)
    return []

def get_articles_from_rss(rss_url):
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title"),
            "url": entry.get("link"),
            "date": entry.get("published", "")
        })
    return articles


def get_article_text(url, page):
    """Extrait le texte complet d’un article (navigateur déjà ouvert)"""
    try:
        sleep_jitter() #pause avant d'ouvrir la page
        page.goto(url, timeout=20000)
        page.wait_for_timeout(2000)
        html = page.content()

        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.select("article p")
        if not paragraphs:
            paragraphs = soup.find_all("p")

        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        return text if text else None
    except Exception as e:
        print(f"[Erreur Playwright] {url} -> {e}")
        return None


def scrape_site(url: str, source: str, limit=None):
    """
    Scrape un site ou flux RSS et retourne une liste d’articles complets.
    - url peut être une page d'accueil ou un flux RSS
    - source = nom du site (ex: 'Artnet', 'ArtNews')
    """
    from playwright.sync_api import sync_playwright

    # essaie de récupérer les articles via RSS ou fallback
    if url.endswith("/feed") or url.endswith(".xml"):
        articles = get_articles_from_rss(url)
    else:
        articles = fetch_source(url)

    if not articles:
        print(f"❌ Aucun article trouvé sur {source}")
        return []

    articles_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = ctx.new_page()

        count = 0
        for art in articles:
            if limit and count >= limit:
                break
            text = get_article_text(art["url"], page)
            if not text:
                continue
            articles_data.append({
                "title": art.get("title", ""),
                "url": art.get("url", ""),
                "date": art.get("date", ""),
                "source": source,
                "content": text
            })
            count += 1
            sleep_jitter(0.6,1.2) #mini pause entre deux articles
        browser.close()

    return articles_data