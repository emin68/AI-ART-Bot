from src.scrap import scrape_site
from src.utils.utils_io import save_json
from src.utils.utils_clean import normalize_articles
from datetime import date
from pathlib import Path
import json
from src.traitement import main as traitement_main
from src.newsletter_sections import main as newsletter_main

# --- Liste des sites à scraper ---
SITES = [
    ("https://news.artnet.com/art-world/science-technology/feed", "Artnet"),
    ("https://www.artnews.com/c/art-news/news/feed/", "ArtNews"),
    ("https://news.artnet.com/market","Artnet market"),
    ("https://news.artnet.com/multimedia","Artnet multimedia"),
    ("https://techcrunch.com/category/artificial-intelligence/", "TechCrunch"),
    ("https://fr.artprice.com/artprice-news","Artprice"),
    ("https://fr.artprice.com/artmarketinsight","ArtPrice ArtMarketInsight"),
    ("https://fr.cointelegraph.com/tags/nft","Cointelegraph NFT"),
    ("https://fr.cointelegraph.com/tags/ai","Cointelegraph AI"),
    ("https://news.artnet.com/multimedia","Dezeen Technology"),
    ("https://www.fastcompany.com/technology","Fastcompany Tech"),
    ("https://www.engadget.com/ai/","Engadget AI"),
    ("https://www.engadget.com/science/robotics/","Engadget robotics")
]


def canonical_url(u: str) -> str:
    """Mini normalisation locale (sans dépendance)"""
    if not u: return ""
    u = u.strip()
    if u.endswith("/"): u = u[:-1]
    return u.lower()

def load_processed_urls(base_dir="data/processed") -> set[str]:
    """Lit toutes les URLs déjà traitées dans processed/**/articles.json"""
    seen = set()
    root = Path(base_dir)
    if not root.exists():
        return seen
    for f in root.glob("**/articles.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for it in data or []:
                cu = canonical_url((it or {}).get("url", ""))
                if cu:
                    seen.add(cu)
        except Exception:
            continue
    return seen

print("🚀 Lancement du scraping multi-sources...\n")

# 0) URLs déjà traitées
already_done = load_processed_urls()
print(f"🧠 URLs déjà traitées trouvées : {len(already_done)}\n")

# 1) Scrape tout (on ne modifie pas scrap.py)
all_articles = []
for url, src in SITES:
    print(f"📰 Scraping {src} ...")
    try:
        arts = scrape_site(url, source=src, limit=5)
        all_articles += arts
        print(f"✅ {len(arts)} articles récupérés depuis {src}\n")
    except Exception as e:
        print(f"⚠️ Erreur sur {src} : {e}\n")

# 2) Filtrer ce qui est déjà traité (post-filtre ultra simple)
new_articles = []
for a in all_articles:
    cu = canonical_url(a.get("url", ""))
    if cu and cu not in already_done:
        new_articles.append(a)

print(f"🆕 Nouveaux articles après filtre : {len(new_articles)}")

# 3) Sauvegarde brute
save_json(new_articles)

# 4) Nettoyage et sauvegarde "processed"
cleaned = normalize_articles(new_articles)
processed_dir = Path("data/processed") / date.today().strftime("%d-%m-%Y")
processed_dir.mkdir(parents=True, exist_ok=True)
processed_path = processed_dir / "articles.json"
with open(processed_path, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"✅ Nettoyage terminé → {processed_path}")
print(f"🧾 Total final (nouveaux uniques) : {len(cleaned)}")

print("\n🧠 Étape suivante : génération des résumés...")
traitement_main()

print("\n📰 Étape suivante : création de la newsletter...")
newsletter_main()

print("\n✅ Pipeline complet terminé ! Newsletter prête dans newsletter.html")