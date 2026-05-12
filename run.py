from app import app
from app.scheduler import start_scheduler
import os

if __name__ == '__main__':
    start_scheduler(app)
    app.run(host='127.0.0.1', port=5000, debug=True)
else:
    # Quando eseguito da Gunicorn, avvia lo scheduler solo nel worker principale
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        start_scheduler(app)