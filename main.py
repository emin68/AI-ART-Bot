# main.py
import json
from datetime import date
from scrap import scrape_artnet_science_tech

def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("🚀 Lancement du scraping Artnet...")
    articles = scrape_artnet_science_tech(limit=5)

    print(f"✅ {len(articles)} articles récupérés.")
    for art in articles:
        print(f"- {art['title']}")

    # Sauvegarde
    today = date.today().isoformat()
    filename = f"data/raw/{today}.json"
    save_to_json(articles, filename)
    print(f"💾 Données sauvegardées dans {filename}")
