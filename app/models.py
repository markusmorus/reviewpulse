from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    places = db.relationship('MonitoredPlace', backref='owner', lazy=True, cascade='all, delete-orphan')
    rules = db.relationship('NotificationRule', backref='owner', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='owner', lazy=True)

class MonitoredPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.String(512), nullable=False)
    place_name = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviews = db.relationship('Review', backref='place', lazy=True, cascade='all, delete-orphan')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    text = db.Column(db.Text)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), default="Google")
    sentiment = db.Column(db.String(20))
    notified = db.Column(db.Boolean, default=False)
    response_sent = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('monitored_place.id'), nullable=False)

class NotificationRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(20))
    target = db.Column(db.String(100))
    trigger_sentiment = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)