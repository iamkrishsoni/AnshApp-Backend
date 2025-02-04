from ..db import db
from datetime import datetime

class BugBountyWallet(db.Model):
    __tablename__ = 'bug_bounty_wallet'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    recommended_points = db.Column(db.Integer, default=0)
    month = db.Column(db.String(7), nullable=False)  # Format: mm-yyyy

    # Relationship to User
    user = db.relationship('User', back_populates='bug_bounty_wallet')

    # Relationship to BountyPoints
    bounty_points = db.relationship('BountyPoints', backref='wallet', lazy=True)

    def __init__(self, user_id, total_points=0, recommended_points=0, month=None):
        self.user_id = user_id
        self.total_points = total_points
        self.recommended_points = recommended_points
        self.month = month or datetime.utcnow().strftime('%m-%Y')
