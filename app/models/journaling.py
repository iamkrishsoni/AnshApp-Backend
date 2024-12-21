from ..db import db
from datetime import datetime

class Journaling(db.Model):
    __tablename__ = 'journaling'

    # Define the columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    day_overall = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(500), nullable=True)
    audio = db.Column(db.String(500), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bg_color = db.Column(db.String(255), default="#ffffff", nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id":self.user_id,
            "title": self.title,
            "description": self.description,
            "day_overall": self.day_overall,
            "image": self.image,
            "audio": self.audio,
            "date": self.date.isoformat(),
            "bg_color":self.bg_color
        }
