from textblob import TextBlob
from config import Config

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

def analyze_sentiment(text, use_gemini=True):
    if not text or not text.strip():
        return "neutral"
    if use_gemini and Config.GEMINI_API_KEY and GENAI_AVAILABLE:
        try:
            client = genai.Client(api_key=Config.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Analizza il sentiment di questa recensione italiana. Rispondi solo con 'positive', 'negative' o 'neutral': {text}"
            )
            return response.text.strip().lower()
        except Exception as e:
            print(f"Errore Gemini: {e}")
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"