from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
from app.models import db, User
import os

login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Per favore accedi per visualizzare questa pagina.'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()
        # Crea admin di default se non esiste
        admin = User.query.filter_by(email='admin@reviewpulse.com').first()
        if not admin:
            admin = User(
                email='admin@reviewpulse.com',
                password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    # Registra i blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Avvia lo scheduler SOLO nel processo principale
    # (evita duplicazione con Gunicorn multi-worker o con il reloader di Flask)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app

# Istanza a livello di modulo per Gunicorn
app = create_app()