# force_check.py
from app import create_app
from app.scheduler import check_all_reviews

app = create_app()
check_all_reviews(app)