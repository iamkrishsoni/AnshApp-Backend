from datetime import datetime
from ..db import db

class PermanentAffirmation(db.Model):
    __tablename__ = 'permanent_affirmations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    affirmation_text = db.Column(db.String(255), nullable=False)
    reminder_active = db.Column(db.Boolean, default=False)  # If reminder is active for this affirmation
    reminder_time = db.Column(db.String(50), nullable=True)  # Time when reminder should trigger
    bg_type = db.Column(db.String(50), nullable=True)  # Type of background (e.g., image, video, color)
    bg_image = db.Column(db.String(255), nullable=True)  # URL or path to the background image
    bg_video = db.Column(db.String(255), nullable=True)  # URL or path to the background video
    affirmation_type = db.Column(db.String(50), nullable=True)  # Type of affirmation (e.g., motivational, gratitude)
    isdark = db.Column(db.Boolean, default=False)  # Indicates if the background is dark
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='permanent_affirmation')

    def __init__(self, affirmation_text, user_id, reminder_active=False, reminder_time=None, bg_type=None, bg_image=None, bg_video=None, affirmation_type=None, isdark=False):
        self.affirmation_text = affirmation_text
        self.user_id = user_id
        self.reminder_active = reminder_active
        self.reminder_time = reminder_time
        self.bg_type = bg_type
        self.bg_image = bg_image
        self.bg_video = bg_video
        self.affirmation_type = affirmation_type
        self.isdark = isdark

    def to_dict(self):
        return {
            "id": self.id,
            "affirmation_text": self.affirmation_text,
            "reminder_active": self.reminder_active,
            "reminder_time": self.reminder_time,
            "bg_type": self.bg_type,
            "bg_image": self.bg_image,
            "bg_video": self.bg_video,
            "affirmation_type": self.affirmation_type,
            "isdark": self.isdark,
            "user_id": self.user_id
        }
