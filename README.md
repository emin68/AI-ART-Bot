# 🧠 Bot AI ART — Automated Art × AI Newsletter Generator
## 🎯 Description

Bot AI ART is an intelligent pipeline that automatically collects, summarizes, and formats weekly news from multiple art and technology sources into a professional magazine-style newsletter.

It merges AI-driven text synthesis with curated web scraping to create an elegant, human-like editorial digest on the intersection of Art × AI × Tech — ready to send as an email or publish online.

## 🧩 Features

✅ Multi-source scraping (Artnet, ArtNews, CoinTelegraph, TechCrunch, Engadget, etc.)  
✅ Automatic data cleaning and deduplication  
✅ Smart summarization using OpenAI GPT models  
✅ Section-based synthesis (NFTs, Auctions, AI, Cloud, etc.)  
✅ Fully formatted HTML newsletter (mobile-friendly)  
✅ Ready for future automation (email sending, scheduling, archiving)  

## 🏗️ Project Architecture
```text
Bot AI ART/
├── data/
│   ├── raw/             # raw scraped articles (by date)
│   ├── processed/       # cleaned and normalized articles
│   ├── treated/         # AI-generated summaries (via GPT)
│   ├── newsletters/     # final HTML newsletter files
│   └── logs/            # error and scraping logs
├── src/
│   ├── main.py          # main pipeline (scraping → summarization → newsletter → email)
│   ├── scrap.py         # RSS/HTML scraping with random delays
│   ├── traitement.py    # generates summaries using GPT-4o-mini
│   ├── newsletter_sections.py  # builds the final magazine-style HTML
│   ├── envoi.py         # sends the generated newsletter via email
│   └── utils/
│       ├── utils_io.py
│       ├── utils_env.py
│       └── utils_clean.py
└── .env                 # configuration file (API key, SMTP credentials, recipients, etc.)

```

## ⚙️ Technologies Used

Category	Technology  
Language	Python 3.10+  
Scraping	requests, feedparser, BeautifulSoup4, lxml  
AI Summarization	OpenAI GPT-4o-mini  
Automation	pathlib, datetime, json  
HTML Generation	Inline CSS + Python string templates  
Environment Management	python-dotenv  
Virtual Environment	venv  
Future Add-ons	Email sending via SMTP or Gmail API, CRON scheduling, Notion/Drive archiving  

## 📦 Installation

### Clone the repo and create your environment:
```bash
git clone https://github.com/emin68/BotAIART.git
cd "BotAIART"
python3 -m venv venv
source venv/bin/activate       # (on Windows: venv\Scripts\activate)
pip install -r requirements.txt
```
🔑 Configuration (.env file)
```bash
Create a .env file at the project root with your configuration:

OPENAI_API_KEY=sk-xxxxxx
OPENAI_MODEL=gpt-4o-mini
```

## Future use (email sending)
```bash
EMAIL_FROM=you@example.com
EMAIL_TO=client@example.com
```
🚀 Usage
1️⃣ Run the full pipeline (Scraping → Summaries → Newsletter)

From the project root:
```bash
python -m src.main

```
### This executes:

- Scraping multiple sources

- Cleaning and deduplication

- Summarization with GPT

- HTML newsletter generation

- Sending mail

### The output will appear as:

✅ Newsletter generated → newsletter_yyyy-mm-dd.html


### If you want to test each phase individually:

## Scraping + normalization
```bash
python -m src.main
```
## Summarization
```bash
python -m src.traitement
```
## Newsletter generation only
```bash
python -m src.newsletter_sections
```
## Sending mail only
```bash
python -m src.envoi
```

## 📅 Typical Weekly Workflow
Step	            Description	                                    Output  
1️⃣ Scraping	    Fetches fresh articles from art & tech feeds	data/raw/    
2️⃣ Processing	    Cleans, filters, removes duplicates	            data/processed/    
3️⃣ Summarization	Creates GPT-based summaries	                    data/treated/    
4️⃣ Newsletter	    Builds an HTML digest	                        newsletter.html    
5️⃣ Send	        Email to recipients 

## 👤 Author

Emin Goktekin  
Founder of Bot AI ART  
📧 emin.gktkn@gmail.com  
🤖 “Bridging creativity and intelligence.”  