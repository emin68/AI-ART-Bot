# src/envoi.py
"""
Envoi automatique de la newsletter HTML générée.
Lit la configuration SMTP et la liste des destinataires depuis le fichier .env.
"""

import os, smtplib, time
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from src.utils.utils_env import load_env, get_env_var
from pathlib import Path

NEWSLETTER_DIR = Path("data/newsletters")

def latest_newsletter() -> Path | None:
    files = list(NEWSLETTER_DIR.glob("newsletter_*.html"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def html_to_text(html: str) -> str:
    """Convertit le HTML en texte brut simplifié (pour clients mail texte)."""
    import re
    text = html
    text = re.sub(r"(?is)<head.*?</head>", "", text)
    text = re.sub(r"(?is)<script.*?</script>", "", text)
    text = re.sub(r"(?is)<style.*?</style>", "", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r'(?is)<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    return text.strip()


def personalize_unsub(html: str, recipient: str) -> str:
    """Personnalise le lien de désinscription."""
    unsub = f"mailto:{get_env_var('SENDER_EMAIL')}?subject=Unsubscribe&body=Please%20remove%20{recipient}"
    return html.replace('href="#"', f'href="{unsub}"')


def send_email(to_email: str, subject: str, html_content: str, sender_name: str, sender_email: str,
               smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str):
    """Envoie un email HTML avec fallback texte brut."""
    text_content = html_to_text(html_content)

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender_email, [to_email], msg.as_string())
            print(f"📨 Mail envoyé à {to_email}")
    except Exception as e:
        print(f"⚠️ Erreur lors de l’envoi à {to_email} : {e}")


def main():
    load_env()

    # 🔹 Lecture des variables d’environnement
    sender_email = get_env_var("SENDER_EMAIL")
    sender_name = get_env_var("SENDER_NAME", "Bot AI ART")
    recipients = get_env_var("RECIPIENT_EMAILS", "").split(",")
    smtp_host = get_env_var("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(get_env_var("SMTP_PORT", "587"))
    smtp_user = get_env_var("SMTP_USER", sender_email)
    smtp_pass = get_env_var("SMTP_PASS")
    newsletter_title = get_env_var("NEWSLETTER_TITLE", "Art & AI Digest – Hebdo")

    # Vérifications
    if not sender_email or not recipients or not smtp_user or not smtp_pass:
        raise RuntimeError("⚠️ Configuration SMTP ou emails incomplète dans le .env")
    
    nl = latest_newsletter()
    if not nl:
        raise FileNotFoundError("⚠️ No newsletter found in data/newsletters/.")
    print(f"📄 Using newsletter: {nl.name}")

    html = nl.read_text(encoding="utf-8")
    
    # 🔹 Lecture du HTML
    today = date.today().strftime("%d-%m-%Y")
    subject = f"{newsletter_title} — {today}"

    print(f"📬 Envoi de la newsletter '{subject}' à {len(recipients)} destinataires...\n")

    for recipient in recipients:
        email = recipient.strip()
        if not email:
            continue
        html_personal = personalize_unsub(html, email)
        send_email(
            to_email=email,
            subject=subject,
            html_content=html_personal,
            sender_name=sender_name,
            sender_email=sender_email,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
        )
        time.sleep(1)  # petite pause entre les envois

    print("\n✅ Envoi terminé avec succès !")


if __name__ == "__main__":
    main()
