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
    month = db.Column(db.String(7), nullable=False)  # Format: mm-yyyy
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, wallet_id, user_id, name, category, points, recommended_points, last_added_points, month, date=None):
        self.wallet_id = wallet_id
        self.user_id = user_id
        self.name = name
        self.category = category
        self.points = points
        self.recommended_points = recommended_points
        self.last_added_points = last_added_points
        self.month = month or datetime.utcnow().strftime('%m-%Y')
        self.date = date or datetime.utcnow()
