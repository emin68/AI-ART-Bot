import json
from datetime import date, datetime
from pathlib import Path
from scrap import scrape_artnet_science_tech


def save_to_json(data, base_dir: str = "data/raw") -> str:
    """
    Crée un sous-dossier daté (ex: data/raw/17-10-2025)
    et enregistre les données dans un fichier JSON horodaté.
    Retourne le chemin du fichier créé.
    """
    # Dossier du jour au format DD-MM-YYYY
    day_folder = Path(base_dir) / date.today().strftime("%d-%m-%Y")
    day_folder.mkdir(parents=True, exist_ok=True)

    # Nom de fichier horodaté pour éviter les écrasements
    ts = datetime.now().strftime("%Hh%Mmin%Ss")
    filename = day_folder / f"artnet_{ts}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(filename)


def main() -> None:
    print("🚀 Lancement du scraping Artnet (Science & Tech)...")

    try:
        articles = scrape_artnet_science_tech(limit=5)
    except Exception as e:
        print(f"❌ Erreur pendant le scraping : {e}")
        return

    nb = len(articles) if isinstance(articles, list) else 0
    print(f"✅ {nb} articles récupérés.")
    for art in articles or []:
        title = (art or {}).get("title", "—")
        print(f"- {title}")

    try:
        filepath = save_to_json(articles or [])
        print(f"💾 Données sauvegardées dans {filepath}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde JSON : {e}")


if __name__ == "__main__":
    main()
