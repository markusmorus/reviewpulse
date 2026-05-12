from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, MonitoredPlace, Review, NotificationRule
from app.scheduler import resolve_short_url, extract_name_from_url

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email già registrata.', 'danger')
            return redirect(url_for('main.register'))
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Registrazione completata. Ora accedi.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Credenziali non valide.', 'danger')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    place_filter = request.args.get('place', type=int)  # id del locale
    places = MonitoredPlace.query.filter_by(user_id=current_user.id).all()
    rules = NotificationRule.query.filter_by(user_id=current_user.id).all()

    reviews_query = Review.query.filter_by(user_id=current_user.id)
    if place_filter:
        reviews_query = reviews_query.filter_by(place_id=place_filter)
    reviews = reviews_query.order_by(Review.time.desc()).all()

    return render_template('dashboard.html',
                           places=places,
                           reviews=reviews,
                           rules=rules,
                           place_filter=place_filter)

@main.route('/force_check')
@login_required
def force_check():
    from app.scheduler import check_all_reviews
    from flask import current_app
    # Forza il controllo per l'utente corrente
    check_all_reviews(current_app._get_current_object())
    flash('Controllo recensioni completato!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/place/<int:place_id>')
@login_required
def place_detail(place_id):
    place = MonitoredPlace.query.get_or_404(place_id)
    # Verifica che l'utente sia proprietario o admin
    if place.user_id != current_user.id and not current_user.is_admin:
        flash('Accesso non autorizzato.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Recupera tutte le recensioni di questo locale
    reviews = Review.query.filter_by(place_id=place.id).order_by(Review.time.desc()).all()

    # Calcola statistiche
    total = len(reviews)
    positive = sum(1 for r in reviews if r.sentiment == 'positive')
    negative = sum(1 for r in reviews if r.sentiment == 'negative')
    neutral = sum(1 for r in reviews if r.sentiment == 'neutral')
    avg_rating = sum(r.rating for r in reviews) / total if total > 0 else 0

    # Preparazione dati per Chart.js (grafico a torta)
    chart_labels = ['Positive', 'Negative', 'Neutral']
    chart_data = [positive, negative, neutral]

    return render_template('place_detail.html',
                           place=place,
                           reviews=reviews,
                           total=total,
                           positive=positive,
                           negative=negative,
                           neutral=neutral,
                           avg_rating=round(avg_rating, 2),
                           chart_labels=chart_labels,
                           chart_data=chart_data)


@main.route('/add_place', methods=['POST'])
@login_required
def add_place():
    user_input = request.form['place_id'].strip()
    place_name = request.form.get('place_name', '').strip()

    # Se è un URL (breve o lungo), proviamo a risolverlo
    final_url = user_input
    if user_input.startswith('http'):
        expanded = resolve_short_url(user_input)
        if expanded:
            final_url = expanded
        else:
            flash('Impossibile risolvere il link. Assicurati che sia valido o incolla il Place ID direttamente.', 'danger')
            return redirect(url_for('main.dashboard'))

    # Se è un Place ID diretto (ChIJ...), lo salviamo così com'è
    # Controllo di base: se non inizia con 'http' e non è un ChIJ valido, potrebbe essere errore
    if not final_url.startswith('http') and not final_url.startswith('ChIJ'):
        flash('Formato non riconosciuto. Inserisci un URL di Google Maps o un Place ID (ChIJ...).', 'danger')
        return redirect(url_for('main.dashboard'))

    place = MonitoredPlace(
        place_id=final_url,
        place_name=place_name if place_name else None,
        user_id=current_user.id
    )
    db.session.add(place)
    db.session.commit()
    flash('Attività aggiunta correttamente.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/remove_place/<int:place_id>')
@login_required
def remove_place(place_id):
    place = MonitoredPlace.query.get_or_404(place_id)
    if place.user_id != current_user.id and not current_user.is_admin:
        flash('Non autorizzato.', 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(place)
    db.session.commit()
    flash('Attività rimossa.', 'info')
    return redirect(url_for('main.dashboard'))

@main.route('/add_rule', methods=['POST'])
@login_required
def add_rule():
    channel = request.form['channel']
    target = request.form['target']
    if not channel or not target:
        flash('Compila tutti i campi.', 'danger')
        return redirect(url_for('main.dashboard'))
    rule = NotificationRule(channel=channel, target=target, trigger_sentiment='negative', user_id=current_user.id)
    db.session.add(rule)
    db.session.commit()
    flash('Regola di notifica aggiunta.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/remove_rule/<int:rule_id>')
@login_required
def remove_rule(rule_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    if rule.user_id != current_user.id and not current_user.is_admin:
        flash('Non autorizzato.', 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(rule)
    db.session.commit()
    flash('Regola rimossa.', 'info')
    return redirect(url_for('main.dashboard'))

@main.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Accesso riservato.', 'danger')
        return redirect(url_for('main.dashboard'))
    users = User.query.all()
    total_places = MonitoredPlace.query.count()
    total_reviews = Review.query.count()
    return render_template('admin.html', users=users, total_places=total_places, total_reviews=total_reviews)

@main.route('/admin/user/<int:user_id>')
@login_required
def admin_view_user(user_id):
    if not current_user.is_admin:
        flash('Accesso riservato.', 'danger')
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(user_id)
    places = MonitoredPlace.query.filter_by(user_id=user.id).all()
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.time.desc()).all()
    rules = NotificationRule.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', places=places, reviews=reviews, rules=rules, view_user=user)