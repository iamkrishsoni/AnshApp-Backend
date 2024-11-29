from ..db import db
from datetime import datetime

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_type = db.Column(db.String(50), nullable=False)  # 'user' or 'professional'
    sender_id = db.Column(db.Integer, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # 'text', 'image', 'video', 'audio'
    message_content = db.Column(db.Text, nullable=True)  # Could be text or media URL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    chat_room = db.relationship('ChatRoom', backref='messages')