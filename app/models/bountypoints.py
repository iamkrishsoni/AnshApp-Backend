from ..db import db
from datetime import datetime

class BountyPoints(db.Model):
    __tablename__ = 'bounty_points'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('bug_bounty_wallet.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    recommended_points = db.Column(db.Integer, nullable=False)
    last_added_points = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
