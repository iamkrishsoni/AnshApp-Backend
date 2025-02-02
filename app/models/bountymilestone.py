from ..db import db
from datetime import datetime

class BountyMilestone(db.Model):
    __tablename__ = 'bounty_milestone'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    milestone = db.Column(db.Integer, nullable=False)  # 1000, 2500, 5000, 10000
    claimed = db.Column(db.Boolean, default=False)  # Track if the reward is claimed
    date_achieved = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='bounty_milestone')