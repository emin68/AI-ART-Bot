# Magazine-style weekly email (EN): narrative sections synthesized from today's summaries

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from utils_env import load_env, get_env_var

TREATED_DIR = Path("data/treated")
OUT_HTML = Path("newsletter.html")
DEFAULT_MODEL = "gpt-4o-mini"

# ---------- Load today's summaries

def load_today_summaries() -> Tuple[str, List[Dict[str, Any]]]:
    today_str = date.today().strftime("%d-%m-%Y")
    fpath = TREATED_DIR / today_str / "summaries.json"
    if not fpath.exists():
        raise FileNotFoundError(f"Missing summaries file: {fpath}")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"No items in {fpath}")
    return today_str, data

# ---------- Buckets (themes)

def _match(text: str, *needles: str) -> bool:
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)

THEMES = [
    ("Tokens & Crypto (NFTs)", ["nft", "crypto", "web3", "token", "blockchain", "coin", "defi"]),
    ("Auctions & Sales (upcoming & results)", ["auction", "sale", "hammer", "sold", "estimate", "christie", "sotheby", "phillips", "bonhams", "catalogue", "lot"]),
    ("Cloud / Platforms & Tools for Art", ["cloud", "saas", "platform", "api", "service", "tool", "hosting", "marketplace", "app"]),
    ("Associations & Foundations (Art × AI/Tech)", ["association", "foundation", "nonprofit", "initiative", "institute", "consortium"]),
    ("AI/Robot Artworks & New Developments", ["robot", "ai art", "generative", "model", "sora", "midjourney", "stable diffusion", "openai", "algorithm", "machine learning", "computer vision"]),
    ("Stats & Analytics (Key Signals)", ["data", "report", "statistics", "analytics", "traffic", "trend", "survey", "by the numbers", "totaled", "percent"]),
    ("Upcoming Art Events (Global)", ["fair", "biennial", "biennale", "exhibition", "opening", "festival", "event", "vip day", "preview", "week", "frieze", "art basel"]),
]

def bucketize(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets = {name: [] for name, _ in THEMES}
    buckets["General / Other"] = []
    for it in items:
        blob = " ".join([
            it.get("title", ""), it.get("summary", ""), it.get("source", ""), it.get("topic", "")
        ])
        placed = False
        for name, keys in THEMES:
            if _match(blob, *keys):
                buckets[name].append(it)
                placed = True
                break
        if not placed:
            buckets["General / Other"].append(it)
    return buckets

# ---------- Payload for LLM

def build_llm_payload(today_str: str, buckets: Dict[str, List[Dict[str, Any]]]) -> str:
    """We pass trimmed items because we want SYNTHESIS, not a link farm."""
    payload = {"date": today_str, "sections": []}
    for section, items in buckets.items():
        if not items:
            continue
        # keep at most 10 items per section as raw material
        trimmed = []
        for it in items[:10]:
            trimmed.append({
                "title": it.get("title", ""),
                "source": it.get("source", ""),
                "date": it.get("date", ""),
                "summary": it.get("summary", ""),
                "url": it.get("url", ""),
            })
        payload["sections"].append({"name": section, "items": trimmed})
    return json.dumps(payload, ensure_ascii=False)

def system_prompt() -> str:
    return (
        "You are a seasoned editor crafting a weekly magazine email at the intersection of Art and AI/Tech. "
        "Write in crisp, confident, professional English for collectors, curators, founders, and analysts. "
        "Prioritize synthesis and signal over enumerating articles."
    )

def user_prompt(json_payload: str) -> str:
    return f"""
You will receive JSON with themed sections and a handful of articles per section.

TASK:
Create a single-column, mobile-friendly HTML email (inline CSS only) that synthesizes the week.

STRICT REQUIREMENTS:
- Language: English. Tone: clear, confident, and analytical — avoid marketing hype.
- Focus on SYNTHESIS per section: explain what's happening now and why it matters.
- Do NOT list all articles. Selectively weave insights into a cohesive story.
- For each section, include at most 2–3 **HTML** inline links using the exact pattern:
  <a href="https://example.com" style="color:#0b66c3;text-decoration:none;">Anchor text</a>
- Never use Markdown links (no [text](url)). Never paste raw URLs; always wrap in <a>.
- Make each section flow naturally into the next, as if part of a single narrative.
- Add 1 strong opening line for the header ("Art and AI/Tech Weekly Digest") and a one-sentence tagline that captures the week's energy.
- End with a short closing remark (“See you next week…”) to make it feel human.

STRUCTURE:
  1) Header: magazine-style masthead with background color bar, issue date, and one-sentence tagline.
  2) Editor’s Note: 5 sentences (or more if there is a lot of article, maximum 8 sentences) setting the tone, summarizing key trends.
  3) Thematic Sections (only those present in JSON):
     - Heading with emoji (🔗, 🖼️, ☁️, 🤖, ⚖️, 📊…).
     - 2–5 compact paragraphs that synthesize developments and add context.
     - Include 1–2 short key figures or quotes if available (for realism).
  4) If a "Stats & Analytics" section exists, display 3–5 concise bullets below it.
  5) Footer: - Do NOT create your own footer. Use this exact footer content:
  “— Edited and curated by Emin Goktekin ✍️ (Founder of Bot AI ART — bridging creativity and intelligence.)”
  Include the email: emin.gktkn@gmail.com and a short unsubscribe link.

DESIGN:
- Clean, elegant, modern magazine lookn use warm color (a little bit of pink too).
- Use a max width around 720px, line-height 1.6.
- Subtle color accents (#0b66c3 or muted blue-gray), separators between sections.
- Section titles larger and bold with a color bar or underline.
- Add a light background on the header and footer for visual balance.

OUTPUT:
Return ONLY the final HTML (no markdown, no code fences).
Ensure it's valid HTML5 and ready to send as email.

JSON INPUT:
{json_payload}
""".strip()


# ---------- Fallback HTML (minimal synthesis-like)

def render_fallback(today_str: str, buckets: Dict[str, List[Dict[str, Any]]]) -> str:
    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    sections_html = []
    for name, items in buckets.items():
        if not items:
            continue
        picks = items[:3]
        sentences = []
        for it in picks:
            t = esc(it.get("title", ""))
            s = esc(it.get("source", ""))
            u = it.get("url", "")
            sentences.append(f'<a href="{u}" style="color:#0b66c3;text-decoration:none;">{t}</a> ({s})')
        body = " • ".join(sentences)
        sections_html.append(f"""
          <section style="margin:32px 0;">
            <h2 style="margin:0 0 10px;padding-left:10px;border-left:6px solid #0b66c3;
                       font-size:20px;color:#0f172a;">{esc(name)}</h2>
            <p style="margin:8px 0;color:#2b2b2b;line-height:1.6;">
              Highlights this week: {body}.
            </p>
            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
          </section>
        """)

    now = datetime.now().strftime("%b %d, %Y")
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Art × AI Weekly — {today_str}</title>
</head>
<body style="margin:0;background:#f6f8fb;">
  <div style="max-width:720px;margin:0 auto;background:#ffffff;
              border-radius:14px;box-shadow:0 8px 24px rgba(0,0,0,0.06);padding:32px;">
    <header style="background:#0b66c3;color:white;padding:14px 20px;
                   border-radius:8px 8px 0 0;margin:-32px -32px 24px -32px;">
      <h1 style="margin:0;font-size:26px;">Art × AI Weekly Digest</h1>
      <div style="font-size:14px;opacity:0.9;">Issue date: {now}</div>
    </header>

    <p style="margin:0 0 18px;color:#2b2b2b;font-size:15px;">
      ⚡ Quick fallback edition — A concise snapshot of this week's AI × Art highlights.
    </p>

    {''.join(sections_html)}

    <footer style="border-top:1px solid #eef1f5;margin-top:30px;padding-top:18px;
               color:#6c7a89;font-size:13px;line-height:1.7;">
        <p style="margin-bottom:10px;">
            — Edited and curated by <b>Emin Goktekin</b> ✍️<br>
            <em>Founder of Bot AI ART — bridging creativity and intelligence.</em>
        </p>
        <p style="margin-top:8px;">
            📬 Contact: <a href="mailto:emin.gktkn@gmail.com" style="color:#0b66c3;text-decoration:none;">
            emin.gktkn@gmail.com</a><br>
            💌 Forward this newsletter to a friend interested in Art & Technology.
        </p>
        <p style="margin-top:12px;font-size:12px;">
            <a href="#" style="color:#0b66c3;text-decoration:none;">Unsubscribe</a> • 
            <a href="#" style="color:#0b66c3;text-decoration:none;">View in browser</a>
        </p>
    </footer>
  </div>
</body>
</html>
""".strip()


# ---------- Save

def save_html(html: str, out_path: Path = OUT_HTML) -> None:
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Newsletter generated → {out_path.resolve()}")

# ---------- Main

def main():
    load_env()
    api_key = get_env_var("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Add it to your .env")

    today_str, items = load_today_summaries()
    buckets = bucketize(items)

    payload = build_llm_payload(today_str, buckets)
    client = OpenAI(api_key=api_key)

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt()},
                {"role": "user", "content": user_prompt(payload)},
            ],
        )
        html = (resp.choices[0].message.content or "").strip()
        if "<html" not in html.lower():
            raise ValueError("Model returned non-HTML content; falling back.")
        save_html(html)
    except Exception as e:
        print(f"⚠️ Generation failed: {e}\n→ Using local fallback synthesis.")
        html = render_fallback(today_str, buckets)
        save_html(html)

if __name__ == "__main__":
    main()
