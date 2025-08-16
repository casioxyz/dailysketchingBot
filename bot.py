import os
import sys
import datetime as dt
from zoneinfo import ZoneInfo

import praw
from openai import OpenAI

# ---- Einstellungen per Umgebungsvariablen ----
CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
USERNAME = os.environ["REDDIT_USERNAME"]
PASSWORD = os.environ["REDDIT_PASSWORD"]
SUBREDDIT = os.environ["SUBREDDIT"]  # z.B. "dein_subreddit"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

POST_HOUR_BERLIN = int(os.environ.get("POST_HOUR_BERLIN", "9"))  # 9 = 09:00
TITLE_PREFIX = os.environ.get("TITLE_PREFIX", "🎨 Täglicher KI-Zeichenprompt")

# ---- Zeit / Titel ----
berlin = ZoneInfo("Europe/Berlin")
now_berlin = dt.datetime.now(berlin)

# Läuft stündlich: nur posten, wenn gerade die Zielstunde ist
# if now_berlin.hour != POST_HOUR_BERLIN:
#     print(f"Nicht Post-Zeit ({now_berlin:%H:%M}). Beende.")
#     sys.exit(0)

date_str = now_berlin.strftime("%d.%m.%Y")
title = f"{TITLE_PREFIX} – {date_str}"

# ---- Reddit-Client ----
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=f"Daily AI Prompt Bot by u/{USERNAME}",
    username=USERNAME,
    password=PASSWORD,
)

subreddit = reddit.subreddit(SUBREDDIT)

# Doppelpost-Schutz: Suche nach heutigem Titel
for s in subreddit.search(f'title:"{title}"', sort="new", time_filter="day"):
    if s.title.strip() == title.strip():
        print("Heutiger Prompt existiert bereits. Beende.")
        sys.exit(0)

# ---- KI: Prompt erzeugen ----
client = OpenAI(api_key=OPENAI_API_KEY)

system_message = (
    "Du bist ein kreativer Zeichenlehrer. "
    "Erzeuge GENAU EINEN Zeichnen-Prompt auf Englisch, 1–2 Sätze. "
    "Enthalten: Charakter(e), Twist/Idee, Stil/Technik oder Einschränkung, interessante Pose oder Perspektive. "
    "Verwende beliebige Zeichenstile, aber nur eigene Charaktere, keine bekannten Original-Charaktere wie Goku oder Naruto. "
    "Keine Listen, keine Erklärungen, nur der Prompt-Text."
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.9,
    max_tokens=150,
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Bitte jetzt den heutigen Prompt."},
    ],
)

prompt_text = resp.choices[0].message.content.strip()

body = (
    f"Todays Prompt: \n\n**{prompt_text}**\n\n"
    f"Post your drawing in the Comments. Have Fun! ✍️"
)

# ---- Posten ----
submission = subreddit.submit(title=title, selftext=body)
print(f"✅ Gepostet: {submission.permalink}")
