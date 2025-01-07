from ..db import db
from datetime import datetime

class Notifications(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    navigation = db.Column(db.String(255), nullable=True)  # Navigation path or URL
    body = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)  # URL or path to the image
    user_id = db.Column(db.Integer, nullable=False)  # Reference to the user receiving the notification
    type = db.Column(db.String(50), nullable=False)  # Type of notification (e.g., info, alert)
    service = db.Column(db.String(50), nullable=False)  # Service triggering the notification
    status = db.Column(db.String(50), nullable=False, default='pending')  # Status (e.g., sent, failed)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    live_until = db.Column(db.DateTime, nullable=True)  # Expiration time for the notification

    def __init__(self, title, description, navigation, body, image, user_id, type, service, status='pending', live_until=None):
        self.title = title
        self.description = description
        self.navigation = navigation
        self.body = body
        self.image = image
        self.user_id = user_id
        self.type = type
        self.service = service
        self.status = status
        self.live_until = live_until

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'navigation': self.navigation,
            'body': self.body,
            'image': self.image,
            'user_id': self.user_id,
            'type': self.type,
            'service': self.service,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'live_until': self.live_until.isoformat() if self.live_until else None
        }
