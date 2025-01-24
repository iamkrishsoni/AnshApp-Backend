from ..db import db
from datetime import datetime

class Mindfulness(db.Model):
    __tablename__ = 'mindfullness'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)  # Title of the mindfulness activity
    description = db.Column(db.String(500), nullable=True)  # Description of the mindfulness activity
    image = db.Column(db.String(255), nullable=True)  # URL or path to image
    audio = db.Column(db.String(255), nullable=True)  # URL or path to audio
    color = db.Column(db.String(7), nullable=True)  # Hex color for UI (e.g., "#ff5733")
    additionalinfo = db.Column(db.String(500), nullable=True)  # Any additional information
    date_added = db.Column(db.DateTime, default=datetime.utcnow)  # Date the record was added, defaults to current date

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "image": self.image,
            "audio": self.audio,
            "color": self.color,
            "additionalinfo": self.additionalinfo,
            "date_added": self.date_added.isoformat()  # Return date in ISO 8601 format
        }
