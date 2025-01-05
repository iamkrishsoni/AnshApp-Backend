from datetime import datetime
from enum import Enum
from ..db import db

class MessageType(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    FILE = 'file'
    DOCUMENT = 'document'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_type = db.Column(db.String(50), nullable=True)  # 'user' or 'professional'
    sender_id = db.Column(db.String(255), nullable=False)  # Unique sender ID (e.g., email or UUID)
    sender_name = db.Column(db.String(100), nullable=False, default="User")  # Sender's name
    message_type = db.Column(db.Enum(MessageType), nullable=False)  # Enum for message types
    message_content = db.Column(db.Text, nullable=True)  # Could be text or media URL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # Track if the message has been read
    is_mentioned = db.Column(db.Boolean, default=False)  # Track if the sender is mentioned
    mentions = db.Column(db.Text, nullable=True)  # List of mentioned users (if any)
    msg_id = db.Column(db.String(255), nullable=False)  # Unique message ID
    from_uid = db.Column(db.String(255), nullable=False)  # Unique ID of the sender
    receipt = db.Column(db.Integer, default=1)  # Read receipt count
    
    # New field for recipient ID
    recipient_id = db.Column(db.String(255), nullable=False)  # Unique recipient ID (e.g., email or UUID)

    # Media-related columns
    attachments = db.relationship('MessageAttachment', backref='chat_message', lazy=True)

    chat_room = db.relationship('ChatRoom', backref='messages')

    def to_dict(self):
        media = {attachment.attachment_type.value: attachment.to_dict() for attachment in self.attachments}
        return {
            "_id": str(self.id),
            "createdAt": self.timestamp.isoformat(),
            "from_uid": self.from_uid,
            "is_mentioned": self.is_mentioned,
            "mentions": self.mentions,
            "msg_id": self.msg_id,
            "name": self.sender_name,
            "receipt": self.receipt,
            "text": self.message_content,
            "media": media,
            "timestamp": int(self.timestamp.timestamp() * 1000),
            "recipient_id":self.recipient_id,
            "user": {
                "_id": self.from_uid,
                "avatar": "",  # Avatar can be added later
                "name": self.sender_name
            }
        }

    @staticmethod
    def from_message_data(data, chat_room_id):
        message = ChatMessage(
            chat_room_id=chat_room_id,
            sender_type=data.get('sender_type'),
            sender_id=data.get('sender_id'),
            sender_name=data.get('sender_name', 'User'),
            message_type=MessageType[data.get('message_type').upper()],
            message_content=data.get('text'),
            timestamp=datetime.utcnow(),
            is_mentioned=data.get('is_mentioned', False),
            mentions=data.get('mentions', ""),
            msg_id=data.get('msg_id'),
            from_uid=data.get('from_uid'),
            receipt=data.get('receipt', 1),
            recipient_id=data.get('recipient_id')  # Set recipient ID
        )
        db.session.add(message)
        db.session.commit()

        # Handle attachments (images, video, audio, etc.)
        if data.get('attachments'):
            for attachment_data in data['attachments']:
                attachment = MessageAttachment.from_attachment_data(attachment_data, message.id)
                db.session.add(attachment)

        db.session.commit()
        return message

class MessageAttachment(db.Model):
    __tablename__ = 'message_attachments'

    id = db.Column(db.Integer, primary_key=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False)
    attachment_type = db.Column(db.Enum(MessageType), nullable=False)  # Type of media (image, video, etc.)
    url = db.Column(db.String(255), nullable=False)  # URL of the uploaded file
    file_name = db.Column(db.String(255), nullable=False)  # Original file name
    file_size = db.Column(db.Integer, nullable=False)  # Size of the file in bytes

    def to_dict(self):
        return {
            "url": self.url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "type": self.attachment_type.value
        }

    @staticmethod
    def from_attachment_data(data, message_id):
        return MessageAttachment(
            chat_message_id=message_id,
            attachment_type=MessageType[data['type'].upper()],
            url=data['url'],
            file_name=data['file_name'],
            file_size=data['file_size'],
        )
