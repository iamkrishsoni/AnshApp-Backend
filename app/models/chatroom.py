from ..db import db
from datetime import datetime

class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    professional_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
