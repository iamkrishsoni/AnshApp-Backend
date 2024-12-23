from flask import Blueprint, request, jsonify
from ..db import db
from datetime import datetime
from ..utils import token_required
from ..models import ChatRoom, ChatMessage
import uuid
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_


chat_bp = Blueprint('chat',__name__)

@chat_bp.route('/chats', methods=['GET'])
def get_chats():
    user_id = request.args.get('user_id')
    role = request.args.get('role')
    print("user_id", user_id)

    if not user_id or not role:
        return jsonify({"message": "User ID and role are required"}), 400

    if role == 'user':
        chats = ChatRoom.query.filter_by(user_id=user_id).all()
    elif role == 'professional':
        chats = ChatRoom.query.filter_by(professional_id=user_id).all()
    else:
        return jsonify({"message": "Invalid role"}), 400

    chat_data = []
    for chat in chats:
        # Get the last message in each chat room
        last_message = ChatMessage.query.filter_by(chat_room_id=chat.id).order_by(ChatMessage.timestamp.desc()).first()

        # Get all messages for the chat room
        messages = ChatMessage.query.filter_by(chat_room_id=chat.id).order_by(ChatMessage.timestamp.asc()).all()

        # Prepare the message details
        message_details = [
            {
                "message_id": message.id,
                "sender_id": message.sender_id,
                "sender_name": message.sender_name,
                "message_type": message.message_type,
                "message_content": message.message_content,
                "timestamp": message.timestamp.isoformat(),
                "is_read": message.is_read,
                "is_mentioned": message.is_mentioned,
                "mentions": message.mentions,
                "image": message.image,
                "receipt": message.reciept,
            }
            for message in messages
        ]
        
        chat_data.append({
            "chat_room_id": chat.id,
            "user_id": chat.user_id,
            "professional_id": chat.professional_id,
            "last_message": last_message.message_content if last_message else None,
            "last_message_time": last_message.timestamp.isoformat() if last_message else None,
            "messages": message_details,  # Include all messages here
        })

    return jsonify({"chats": chat_data}), 200

@chat_bp.route('/chats/<int:chat_room_id>/messages', methods=['GET'])
def get_chat_messages(chat_room_id):
    # Retrieve all messages for a specific chat room
    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        print("Chat room not found")
        return jsonify({"message": "Chat room not found"}), 404

    # Retrieve all messages in the chat room, ordered by timestamp
    messages = ChatMessage.query.filter_by(chat_room_id=chat_room_id).order_by(ChatMessage.timestamp.asc()).all()
    
    # Convert messages to dictionary format
    messages_list = [msg.to_dict() for msg in messages]
    
    return jsonify({
        "chat_room_id": chat_room.id,
        "messages": messages_list
    }), 200


@chat_bp.route('/chats/<int:chat_room_id>/message', methods=['POST'])
@token_required
def send_message(current_user,chat_room_id):
    data = request.get_json()
    
    # Extract sender details from the request data
    sender_id = data.get('sender_id')  # Authenticated user's ID, passed in the request
    role = data.get('role')  # 'user' or 'professional'

    # Validate input
    message_type = data.get('message_type')  # 'text', 'image', 'video', 'audio'
    message_content = data.get('message_content')
    timestamp= data.get('timestamp')

    if not message_type or not message_content or not sender_id or not role:
        return jsonify({"message": "Sender ID, role, message type, and content are required"}), 400

    # Validate chat room
    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    # Check if the sender has permission to send a message
    if role == 'user' and chat_room.user_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403
    elif role == 'professional' and chat_room.professional_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403

    # Fetch sender's name (either user or professional)
    sender_name = None
    if role == 'user':
        sender_name = "User"  # Replace with logic to get the actual user name if needed
    elif role == 'professional':
        sender_name = "Professional"  # Replace with logic to get the actual professional name if needed

    # Generate a unique message ID (msg_id)
    msg_id = str(uuid.uuid4())

    # Create the new message
    new_message = ChatMessage(
        chat_room_id=chat_room_id,
        sender_type=role,
        sender_id=sender_id,
        sender_name=sender_name,
        message_type=message_type,
        message_content=message_content,
        timestamp=timestamp,
        msg_id=msg_id,
        from_uid=sender_id,  # Use sender's unique ID in the format required
        reciept=1  # Assuming the message has been read when sent, adjust based on your logic
    )

    db.session.add(new_message)
    db.session.commit()

    # Retrieve all messages in the chat room in the format expected by GiftedChat
    messages = ChatMessage.query.filter_by(chat_room_id=chat_room_id).order_by(ChatMessage.timestamp.asc()).all()
    messages_list = [msg.to_dict() for msg in messages]

    # Return the response in the expected format
    return jsonify({
        "chat_room": {
            "id": chat_room.id,
            "user_id": chat_room.user_id,
            "professional_id": chat_room.professional_id,
            "created_at": chat_room.created_at.isoformat(),
            "messages": messages_list
        },
        "message": "Message sent successfully"
    }), 201
    


@chat_bp.route('/chats/create', methods=['POST'])
@token_required
def create_chat_room(current_user):
    data = request.get_json()
    user_id = data.get('user_id')
    professional_id = data.get('professional_id')

    if not user_id or not professional_id:
        return jsonify({"message": "User ID and Professional ID are required"}), 400

    # Normalize user_id and professional_id (e.g., trim whitespace and convert to string)
    user_id = str(user_id).strip()
    professional_id = str(professional_id).strip()

    # Check if chat room exists
    chat_room = ChatRoom.query.filter(and_(
        ChatRoom.user_id == user_id,
        ChatRoom.professional_id == professional_id
    )).first()

    if chat_room:
        return jsonify({"data": {"chat_room_id": chat_room.id}}), 200
    else:
        chat_room = ChatRoom(user_id=user_id, professional_id=professional_id)
        db.session.add(chat_room)
        db.session.commit()
        return jsonify({"data": {"chat_room_id": chat_room.id}}), 200




@chat_bp.route('/chats/<int:chat_room_id>/read', methods=['POST'])
@token_required
def mark_messages_read(chat_room_id):
    sender_id = request.user_data.get('user_id')
    role = request.user_data.get('role')

    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    if role == 'user' and chat_room.user_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403
    elif role == 'professional' and chat_room.professional_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403

    # Mark messages as read
    ChatMessage.query.filter_by(chat_room_id=chat_room_id, is_read=False).update({"is_read": True})
    db.session.commit()

    return jsonify({"message": "Messages marked as read"}), 200
