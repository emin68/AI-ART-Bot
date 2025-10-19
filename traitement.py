# traitement.py
# V2: test sur UN SEUL article → envoie au LLM OpenAI → sauvegarde un JSON propre
# Usage:
#   python3 traitement.py                 # prend le 1er article du jour
#   python3 traitement.py --index 2       # prend l’article d’index 2
#   python3 traitement.py --date 19-10-2025  # lit les articles de cette date

import argparse
import json
import re
import os
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any
from openai import OpenAI

# ====== CONFIG ======
MODEL = "gpt-4o-mini"
PROCESSED_DIR = Path("data/processed")
TREATED_DIR = Path("data/treated")
TREATED_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== UTILS ======
def extract_first_json_block(text: str) -> Optional[str]:
    """
    Extrait le premier bloc JSON { ... } d’un texte.
    Ignore les ```json``` éventuels et gère les accolades imbriquées.
    """
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
    fpath = PROCESSED_DIR / processed_date / "articles.json"
    if not fpath.exists():
        raise FileNotFoundError(f"Fichier introuvable: {fpath}")
    with open(fpath, "r", encoding="utf-8") as f:
        articles = json.load(f)
    if not isinstance(articles, list) or not articles:
        raise ValueError(f"Aucun article valide dans: {fpath}")
    return articles


def build_prompt(article: Dict[str, Any]) -> str:
    """
    Prompt strict: demande du JSON uniquement.
    """
    title = article.get("title", "Untitled")
    source = article.get("source", "Unknown")
    content = article.get("content", "")

    return f"""
You are an assistant specialized in summarizing English news articles about AI, art, and technology.
Do not invent or add facts that are not explicitly in the article.

Summarize the following article in 2–3 short paragraphs.
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


def run_openai(prompt: str, model: str = MODEL) -> str:
    """
    Envoie le prompt à OpenAI et récupère la réponse complète (texte brut).
    """
    response = client.chat.completions.create(
        model=model,
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
    parser = argparse.ArgumentParser(description="Traitement LLM d'un seul article (OpenAI).")
    parser.add_argument("--date", help="Date du dossier processed au format JJ-MM-AAAA (défaut: aujourd'hui)")
    parser.add_argument("--index", type=int, default=0, help="Index de l'article à traiter (défaut: 0)")
    args = parser.parse_args()

    processed_date = args.date or date.today().strftime("%d-%m-%Y")

    print("🧠 Chargement des articles…")
    articles = load_articles(processed_date)

    if args.index < 0 or args.index >= len(articles):
        raise IndexError(f"Index {args.index} hors limites (0..{len(articles)-1})")

    article = articles[args.index]
    print(f"📄 Article #{args.index} : {article.get('title','Untitled')[:90]}")

    prompt = build_prompt(article)
    print("⚙️ Envoi à OpenAI…")
    raw = run_openai(prompt)
    
    if not raw.strip().endswith("}"):
        raw += "}"  # tente de fermer le JSON tronqué
        
    json_block = extract_first_json_block(raw)
    if not json_block:
        debug_path = TREATED_DIR / "test_one_raw.txt"
        debug_path.write_text(raw, encoding="utf-8")
        raise RuntimeError(f"Aucun JSON détecté. Sortie brute sauvegardée dans {debug_path}")

    try:
        parsed = json.loads(json_block)
    except json.JSONDecodeError:
        (TREATED_DIR / "test_one_raw.txt").write_text(raw, encoding="utf-8")
        (TREATED_DIR / "test_one_block.txt").write_text(json_block, encoding="utf-8")
        raise

    out_path = TREATED_DIR / "test_one.json"
    save_json(parsed, out_path)
    print(f"✅ Résumé sauvegardé proprement → {out_path}")


if __name__ == "__main__":
    main()
