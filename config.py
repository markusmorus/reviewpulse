import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
# Per sviluppo locale, se non c'è DATABASE_URL usa SQLite
default_db = 'sqlite:///' + os.path.join(basedir, 'app', 'reviews.db')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APIFY_API_KEY = os.getenv('APIFY_API_KEY')

    TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP = os.getenv('TWILIO_WHATSAPP_NUMBER')

    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASS = os.getenv('EMAIL_PASS')

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')