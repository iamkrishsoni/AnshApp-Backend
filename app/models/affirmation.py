from ..db import db
from datetime import datetime

class DailyAffirmation(db.Model):
    __tablename__ = 'daily_affirmations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    affirmation_text = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(50), default=datetime.utcnow().strftime('%Y-%m-%d'), nullable=False)
    reminder_active = db.Column(db.Boolean, default=False)  # If reminder is active for this affirmation
    reminder_time = db.Column(db.String(50), nullable=True)  # Time when reminder should trigger
    bg_image = db.Column(db.String(255), nullable=True)  # URL/path of the background image
    liked = db.Column(db.Boolean, default=False)  # Whether the affirmation is liked
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Creation timestamp

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='daily_affirmations')

    def __init__(self, affirmation_text, user_id, date=None, reminder_active=False, reminder_time=None, bg_image=None, liked=False):
        self.affirmation_text = affirmation_text
        self.user_id = user_id
        self.date = date or datetime.utcnow().strftime('%Y-%m-%d')
        self.reminder_active = reminder_active
        self.reminder_time = reminder_time
        self.bg_image = bg_image
        self.liked = liked
        self.created_at = datetime.utcnow()  # Set creation timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "affirmation_text": self.affirmation_text,
            "date": self.date,
            "reminder_active": self.reminder_active,
            "reminder_time": self.reminder_time,
            "bg_image": self.bg_image,
            "liked": self.liked,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }
