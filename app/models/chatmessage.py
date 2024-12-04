from datetime import datetime
from ..db import db

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_type = db.Column(db.String(50), nullable=True)  # 'user' or 'professional'
    sender_id = db.Column(db.String(255), nullable=False)  # Unique sender ID (e.g., email or UUID)
    sender_name = db.Column(db.String(100), nullable=False, default="User")  # Sender's name
    message_type = db.Column(db.String(50), nullable=False)  # 'text', 'image', 'video', 'audio'
    message_content = db.Column(db.Text, nullable=True)  # Could be text or media URL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)  # Track if the message has been read
    is_mentioned = db.Column(db.Boolean, default=False)  # Track if the sender is mentioned
    mentions = db.Column(db.Text, nullable=True)  # List of mentioned users (if any)
    msg_id = db.Column(db.String(255), nullable=False)  # Unique message ID
    from_uid = db.Column(db.String(255), nullable=False)  # Unique ID of the sender
    image = db.Column(db.String(255), nullable=True)  # URL of the image (if message type is 'image')
    reciept = db.Column(db.Integer, default=1)  # Read receipt count

    chat_room = db.relationship('ChatRoom', backref='messages')

    def to_dict(self):
        return {
            "_id": str(self.id),  # Unique ID for the message
            "createdAt": self.timestamp.isoformat(),  # ISO timestamp for message creation
            "from_uid": self.from_uid,  # Sender's unique ID
            "image": self.image,  # URL for image if available
            "is_mentioned": self.is_mentioned,  # If user was mentioned
            "mentions": self.mentions,  # List of mentions
            "msg_id": self.msg_id,  # Unique message ID
            "name": self.sender_name,  # Sender's name
            "reciept": self.reciept,  # Receipt count (read status)
            "text": self.message_content,  # Message content
            "timestamp": int(self.timestamp.timestamp() * 1000),  # Timestamp in milliseconds
            "user": {
                "_id": self.from_uid,  # Sender's unique ID
                "avatar": "",  # Avatar can be added later
                "name": self.sender_name  # Sender's name
            }
        }

    @staticmethod
    def from_message_data(data, chat_room_id):
        """ 
        Create a ChatMessage instance from the incoming message data 
        for sending messages
        """
        message = ChatMessage(
            chat_room_id=chat_room_id,
            sender_type=data.get('sender_type'),
            sender_id=data.get('sender_id'),
            sender_name=data.get('sender_name', 'User'),
            message_type=data.get('message_type'),
            message_content=data.get('text'),
            timestamp=datetime.utcnow(),
            is_mentioned=data.get('is_mentioned', False),
            mentions=data.get('mentions', ""),
            msg_id=data.get('msg_id'),
            from_uid=data.get('from_uid'),
            image=data.get('image', None),
            reciept=data.get('reciept', 1),
        )
        db.session.add(message)
        db.session.commit()
        return message
