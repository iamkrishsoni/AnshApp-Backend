from ..db import db
from datetime import datetime

class Notifications(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    navigation = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    service = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    is_read = db.Column(db.Boolean, default=False)  # ✅ New field to track if notification is read
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    live_until = db.Column(db.DateTime, nullable=True)

    def __init__(self, title, description, navigation, body, image, user_id, type, service, status='pending', live_until=None, is_read=False):
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
        self.is_read = is_read

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
            'is_read': self.is_read,  # ✅ Include is_read in the response
            'created_at': self.created_at.isoformat(),
            'live_until': self.live_until.isoformat() if self.live_until else None
        }
