from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from apify_client import ApifyClient
import requests
import re
from urllib.parse import unquote, urlparse, parse_qs
from config import Config
from app.models import db, MonitoredPlace, Review, NotificationRule
from app.sentiment import analyze_sentiment
from app.notifications import send_whatsapp, send_email

# ---------- Risoluzione URL breve ----------
def resolve_short_url(short_url, timeout=10):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    expanded = None
    # Tentativo 1: HTTP diretto
    try:
        r = requests.get(short_url, headers=headers, allow_redirects=True, timeout=timeout)
        if r.url != short_url:
            expanded = r.url
    except Exception as e:
        print(f"Errore HTTP: {e}")

    # Tentativo 2: unshorten.me
    if not expanded:
        try:
            api_url = f"https://unshorten.me/api/v2/unshorten?url={short_url}"
            resp = requests.get(api_url, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("resolved_url"):
                    expanded = data["resolved_url"]
        except Exception as e:
            print(f"Errore unshorten.me: {e}")

    if not expanded:
        return None

    # Gestione pagina di consenso
    if 'consent.google.com' in expanded:
        parsed = urlparse(expanded)
        params = parse_qs(parsed.query)
        if 'continue' in params:
            expanded = unquote(params['continue'][0])
    return expanded

def extract_name_from_url(url):
    match = re.search(r'/place/([^/@]+)', url)
    if match:
        name = match.group(1).replace('+', ' ')
        try:
            name = unquote(name)
        except:
            pass
        return name
    return None

# ---------- Recupero recensioni Apify ----------
def get_apify_reviews(api_key, place_input):
    if not place_input.startswith('http'):
        place_url = f"https://www.google.com/maps/place/?q=place_id:{place_input}"
    else:
        place_url = place_input

    client = ApifyClient(api_key)
    actor = client.actor("compass~google-maps-reviews-scraper")
    run_input = {
        "startUrls": [{"url": place_url}],
        "maxReviews": 50,
        "reviewsSort": "newest",
        "language": "it",
        "includeReviews": True,
    }
    run = actor.call(run_input=run_input)
    reviews_data = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    normalized_reviews = []
    for r in reviews_data:
        text = r.get('text') or ''
        if not text.strip():
            continue
        normalized_reviews.append({
            'author_name': r.get('name', 'Anonimo'),
            'rating': r.get('stars'),
            'text': text,
            'time': r.get('publishedAtDate')
        })
    return {'reviews': normalized_reviews}, None

# ---------- Controllo principale ----------
def check_all_reviews(app):
    with app.app_context():
        places = MonitoredPlace.query.all()
        if not places:
            return
        for place in places:
            entry = place.place_id
            if not Config.APIFY_API_KEY:
                print("Nessuna chiave Apify configurata.")
                return

            print(f"[Apify] Controllo {place.place_name or entry}...")
            data, error = get_apify_reviews(Config.APIFY_API_KEY, entry)
            if error:
                print(f"Errore Apify: {error}")
                continue

            # Aggiorna nome se assente
            if not place.place_name and entry.startswith('http'):
                name = extract_name_from_url(entry)
                if name:
                    place.place_name = name
                    db.session.commit()

            reviews_list = data.get('reviews', [])
            for r in reviews_list:
                author = r.get('author_name', 'Anonimo')
                text = r.get('text', '') or ''
                if not text.strip():
                    continue

                existing = Review.query.filter_by(
                    author_name=author,
                    text=text,
                    place_id=place.id,
                    user_id=place.user_id
                ).first()
                if existing:
                    continue

                sentiment = analyze_sentiment(text)
                rating = r.get('rating', 0)
                raw_time = r.get('time')
                if isinstance(raw_time, (int, float)):
                    timestamp = datetime.fromtimestamp(raw_time)
                elif isinstance(raw_time, str):
                    timestamp = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.utcnow()

                new_review = Review(
                    author_name=author,
                    rating=rating,
                    text=text,
                    time=timestamp,
                    sentiment=sentiment,
                    user_id=place.user_id,
                    place_id=place.id
                )
                db.session.add(new_review)
                db.session.commit()

                if sentiment == 'negative':
                    rules = NotificationRule.query.filter_by(
                        user_id=place.user_id,
                        trigger_sentiment='negative'
                    ).all()
                    for rule in rules:
                        nome_locale = place.place_name or entry
                        message = f"⚠️ Nuova recensione negativa per {nome_locale}\n{author} ({rating}★): {text}"
                        try:
                            if rule.channel == 'whatsapp':
                                send_whatsapp(rule.target, message)
                            elif rule.channel == 'email':
                                send_email(rule.target, "Recensione negativa", message)
                        except Exception as e:
                            print(f"Notifica fallita: {e}")
                        else:
                            new_review.notified = True
                            db.session.commit()

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_all_reviews, args=[app], trigger="interval", minutes=15)
    scheduler.start()
    import atexit
    atexit.register(lambda: scheduler.shutdown())