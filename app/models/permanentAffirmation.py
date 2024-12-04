from datetime import datetime
from ..db import db

class PermanentAffirmation(db.Model):
    __tablename__ = 'permanent_affirmations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    affirmation_text = db.Column(db.String(255), nullable=False)
    reminder_active = db.Column(db.Boolean, default=False)  # If reminder is active for this affirmation
    reminder_time = db.Column(db.String(50), nullable=True)  # Time when reminder should trigger
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='permanent_affirmation')

    def __init__(self, affirmation_text, user_id, reminder_active=False, reminder_time=None):
        self.affirmation_text = affirmation_text
        self.user_id = user_id
        self.reminder_active = reminder_active
        self.reminder_time = reminder_time

    def to_dict(self):
        return {
            "id": self.id,
            "affirmation_text": self.affirmation_text,
            "reminder_active": self.reminder_active,
            "reminder_time": self.reminder_time,
            "user_id": self.user_id
        }
