# traitement.py
# V3 : traite TOUS les articles → envoie à OpenAI → crée summaries.json

import json
import re
import os
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any
from time import sleep
from openai import OpenAI
from utils_env import load_env, get_env_var


# ====== CONFIG ======
MODEL = "gpt-4o-mini"
PROCESSED_DIR = Path("data/processed")
TREATED_DIR = Path("data/treated")
TREATED_DIR.mkdir(parents=True, exist_ok=True)

# 🔹 Charger les variables d'environnement (.env)
load_env()
# 🔹 Initialiser le client OpenAI
client = OpenAI(api_key=get_env_var("OPENAI_API_KEY"))
print("🔐 Clé OpenAI chargée depuis .env")

# ====== UTILS ======
def extract_first_json_block(text: str) -> Optional[str]:
    """Extrait le premier bloc JSON { ... } d’un texte."""
    if not text:
        return None

    fence_matches = list(re.finditer(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE))
    if fence_matches:
        content = max((m.group(1) for m in fence_matches), key=lambda s: len(s) if s else 0, default="")
        text = content or text

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1].strip()
    return None


def load_articles(processed_date: str) -> list:
    """Charge les articles nettoyés du jour."""
    fpath = PROCESSED_DIR / processed_date / "articles.json"
    if not fpath.exists():
        raise FileNotFoundError(f"Fichier introuvable: {fpath}")
    with open(fpath, "r", encoding="utf-8") as f:
        articles = json.load(f)
    if not isinstance(articles, list) or not articles:
        raise ValueError(f"Aucun article valide dans: {fpath}")
    return articles


def build_prompt(article: Dict[str, Any]) -> str:
    """Construit le prompt JSON strict."""
    title = article.get("title", "Untitled")
    source = article.get("source", "Unknown")
    content = article.get("content", "")

    return f"""
You are an assistant specialized in summarizing English news articles about AI, art, and technology.
Do not invent or add facts that are not explicitly in the article. 
If the text is in another language, translate it correctly in English.

Summarize the following article in two or three short paragraphs.
Keep it factual, concise, and neutral (journalistic tone).
Return your answer as VALID JSON ONLY (no markdown, no extra text, no backticks).
Use exactly this schema and keys:
{{
  "title": "...",
  "source": "...",
  "summary": "...",
  "topic": "...",
  "tags": ["...", "...", "..."]
}}

ARTICLE:
Title: {title}
Source: {source}
Content: {content}
""".strip()


def run_openai(prompt: str) -> str:
    """Appel à l’API OpenAI."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def save_json(data: Dict[str, Any], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ====== MAIN ======
def main():
    today = date.today().strftime("%d-%m-%Y")
    print(f"🧠 Chargement des articles du {today}…")
    articles = load_articles(today)

    results = []
    errors = []

    for i, article in enumerate(articles, start=1):
        title = article.get("title", "Untitled")
        print(f"\n📰 [{i}/{len(articles)}] {title[:80]}")

        try:
            prompt = build_prompt(article)
            raw = run_openai(prompt)

            if not raw.strip().endswith("}"):
                raw += "}"  # corrige JSON tronqué

            json_block = extract_first_json_block(raw)
            if not json_block:
                raise ValueError("Aucun JSON détecté")

            parsed = json.loads(json_block)

            # 🆕 enrichir avec URL et date
            parsed["url"] = article.get("url", "")
            parsed["date"] = article.get("date", "")

            results.append(parsed)
            print("✅ Résumé ajouté")

        except Exception as e:
            print(f"⚠️ Erreur sur l’article {i}: {e}")
            errors.append({"index": i, "title": title, "error": str(e)})

        sleep(1)  # pause pour éviter de saturer l’API

    # Sauvegarde
    out_dir = TREATED_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summaries.json"
    save_json(results, out_path)
    print(f"\n💾 {len(results)} résumés sauvegardés dans {out_path}")

    if errors:
        err_path = out_dir / "errors.json"
        save_json(errors, err_path)
        print(f"⚠️ {len(errors)} erreurs sauvegardées dans {err_path}")

    print("\n🎯 Traitement terminé.")


if __name__ == "__main__":
    main()
