import argparse, os, time, random, json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from src.scrap import scrape_site
from src.utils.utils_io import save_json
from src.utils.utils_clean import normalize_articles
from src.traitement import main as traitement_main
from src.newsletter_sections import main as newsletter_main
from src.envoi import main as envoi_main


# --- Liste des sites à scraper ---
SITES = [
    ("https://news.artnet.com/art-world/science-technology/feed", "Artnet"),
    ("https://www.artnews.com/c/art-news/news/feed/", "ArtNews"),
    ("https://news.artnet.com/market", "Artnet market"),
    ("https://news.artnet.com/multimedia", "Artnet multimedia"),
    ("https://techcrunch.com/category/artificial-intelligence/", "TechCrunch"),
    ("https://fr.cointelegraph.com/tags/nft", "Cointelegraph NFT"),
    ("https://fr.cointelegraph.com/tags/ai", "Cointelegraph AI"),
]

# --- Gestion du cache ---
CACHE_FILE = Path("data/cache/seen_urls.txt")
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_seen_urls():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def update_seen_cache(urls):
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")

def canonical_url(u: str) -> str:
    """Nettoie les URLs (enlève tracking, fragments, normalise)"""
    if not u:
        return ""
    u = u.strip()
    p = urlparse(u)
    path = p.path[:-1] if p.path.endswith("/") and p.path != "/" else p.path
    blacklist = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content",
                 "gclid","fbclid","ref","mc_cid","mc_eid"}
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in blacklist]
    canon = urlunparse((
        p.scheme.lower(),
        p.netloc.lower(),
        path,
        "",  # params
        urlencode(q, doseq=True),
        ""   # fragment
    ))
    return canon


# --- Début du pipeline ---
print("🚀 Lancement du scraping multi-sources...\n")

# 0️⃣ URLs déjà traitées
already_done = load_seen_urls()
print(f"🧠 URLs déjà traitées trouvées dans le cache : {len(already_done)}\n")

# 1️⃣ Scraping des sources
all_articles = []
for url, src in SITES:
    print(f"📰 Scraping {src} ...")
    try:
        arts = scrape_site(url, source=src, limit=5)
        all_articles += arts
        print(f"✅ {len(arts)} articles récupérés depuis {src}\n")
        time.sleep(random.uniform(1.5, 2.5))
    except Exception as e:
        print(f"⚠️ Erreur sur {src} : {e}\n")

# 2️⃣ Filtrer les articles déjà connus
new_articles = []
for a in all_articles:
    cu = canonical_url(a.get("url", ""))
    if cu and cu not in already_done:
        new_articles.append(a)

print(f"🆕 Nouveaux articles après filtre : {len(new_articles)}")

# 3️⃣ Mettre à jour le cache
if new_articles:
    update_seen_cache([canonical_url(a["url"]) for a in new_articles])
    print(f"🧩 Cache mis à jour avec {len(new_articles)} nouvelles URLs.\n")
else:
    print("😴 Aucun nouvel article à ajouter au cache.\n")

# 4️⃣ Sauvegarde brute
save_json(new_articles)

# 5️⃣ Nettoyage + sauvegarde
cleaned = normalize_articles(new_articles)
if len(cleaned) == 0:
    print("⚠️ Aucun nouvel article aujourd'hui. Utilisation des derniers articles disponibles.")

processed_dir = Path("data/processed") / date.today().strftime("%d-%m-%Y")
processed_dir.mkdir(parents=True, exist_ok=True)
processed_path = processed_dir / "articles.json"

with open(processed_path, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"✅ Nettoyage terminé → {processed_path}")
print(f"🧾 Total final (nouveaux uniques) : {len(cleaned)}")

# 6️⃣ Étapes IA & envoi
print("\n🧠 Étape suivante : génération des résumés...")
traitement_main()

print("\n📰 Étape suivante : création de la newsletter...")
newsletter_main()

print("\n✅ Pipeline complet terminé ! Newsletter enregistrée dans data/newsletters/")

if os.getenv("SEND_EMAIL", "true").lower() == "true":
    print("\n📧 Début de l'envoi")
    envoi_main()
    print("\n✅ Mail envoyé")
else:
    print("\n✉️ Envoi désactivé (SEND_EMAIL=false)")
