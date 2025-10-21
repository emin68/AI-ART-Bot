from hashlib import md5


# verifie si un artile existe déja ou pas et agit en conséquences

def normalize_articles(articles):
    cleaned, seen = [], set()
    for art in articles:
        title = (art.get("title") or "").strip().lower()
        url = (art.get("url") or art.get("link") or "").strip().lower()

        key = md5((title + "|" + url).encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)

        cleaned.append({
            "title": art.get("title", "").strip(),
            "url": url,
            "summary": (art.get("summary") or "").strip(),
            "image": (art.get("image") or "").strip(),
            "date": (art.get("date") or "").strip(),
            "source": art.get("source", "Artnet")
        })
    return cleaned
