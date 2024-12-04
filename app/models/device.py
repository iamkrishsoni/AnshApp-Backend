from datetime import datetime
from ..db import db

class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_name = db.Column(db.String(255), nullable=False)
    device_model = db.Column(db.String(255), nullable=False)
    device_os = db.Column(db.String(50), nullable=False)
    device_os_version = db.Column(db.String(50), nullable=False)
    device_id = db.Column(db.String(255), nullable=False)  # Device unique ID
    fcm_token = db.Column(db.String(255), nullable=True)  # FCM token for push notifications
    device_manufacturer = db.Column(db.String(255), nullable=True)
    device_screen_size = db.Column(db.String(50), nullable=True)
    device_resolution = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to User model
    user = db.relationship('User', back_populates='device', uselist=False)

    def __repr__(self):
        return f'<Device {self.device_id}>'
