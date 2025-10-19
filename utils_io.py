import json, hashlib, shutil
from datetime import date, datetime
from pathlib import Path

#lis le dernier fichier dans "data/raw" si y'en a pas le crée
#créer un dossier avec la date du jour et y mets les articles recup

def _hash(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def save_json(data, base="data/raw"):
    Path(base).mkdir(parents=True, exist_ok=True)

    # lire latest.json si présent
    latest = Path(base) / "latest.json"
    old_hash = _hash(json.load(open(latest))) if latest.exists() else None
    new_hash = _hash(data)

    if old_hash == new_hash:
        print("♻️ Pas de changement, pas de nouveau fichier.")
        return str(latest)

    # sinon on crée un nouveau fichier daté
    folder = Path(base) / date.today().strftime("%d-%m-%Y")
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Hh%Mmin%Ss")
    path = folder / f"artnet_{ts}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    shutil.copy(path, latest)
    print(f"💾 Fichier sauvegardé → {path}")
    return str(path)
