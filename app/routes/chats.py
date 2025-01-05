from flask import Blueprint, request, jsonify
from ..db import db
from datetime import datetime
from ..utils import token_required
from ..models import ChatRoom, ChatMessage, MessageAttachment, User, Professional
import uuid
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_

chat_bp = Blueprint('chat', __name__)

# Retrieve all chats for a user or professional
@chat_bp.route('/chats', methods=['GET'])
def get_chats():
    user_id = request.args.get('user_id')
    role = request.args.get('role')

    if not user_id or not role:
        return jsonify({"message": "User ID and role are required"}), 400

    # Fetch chats based on role
    if role == 'user':
        chats = ChatRoom.query.filter_by(user_id=user_id).all()
    elif role == 'professional':
        chats = ChatRoom.query.filter_by(professional_id=user_id).all()
    else:
        return jsonify({"message": "Invalid role"}), 400

    # Prepare chat data
    chat_data = []
    for chat in chats:
        last_message = ChatMessage.query.filter_by(chat_room_id=chat.id).order_by(ChatMessage.timestamp.desc()).first()
        messages = ChatMessage.query.filter_by(chat_room_id=chat.id).order_by(ChatMessage.timestamp.asc()).all()

        chat_data.append({
            "chat_room_id": chat.id,
            "user_id": chat.user_id,
            "professional_id": chat.professional_id,
            "last_message": last_message.message_content if last_message else None,
            "last_message_time": last_message.timestamp.isoformat() if last_message else None,
            "messages": [
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
                    "receipt": message.receipt,
                }
                for message in messages
            ],
        })

    return jsonify({"chats": chat_data}), 200

# Retrieve messages for a specific chat room
@chat_bp.route('/chats/<int:chat_room_id>/messages', methods=['GET'])
def get_chat_messages(chat_room_id):
    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    messages = ChatMessage.query.filter_by(chat_room_id=chat_room_id).order_by(ChatMessage.timestamp.asc()).all()
    messages_list = [message.to_dict() for message in messages]
    print(messages_list)

    return jsonify({"chat_room_id": chat_room.id, "messages": messages_list}), 200

# Send a new message in a chat room
@chat_bp.route('/chats/<int:chat_room_id>/message', methods=['POST'])
@token_required
def send_message(current_user, chat_room_id):
    data = request.get_json()

    sender_id = data.get('sender_id')
    role = data.get('role')
    message_type = data.get('message_type').upper()
    message_content = data.get('message_content')
    timestamp = data.get('timestamp')

    if not sender_id or not role or not message_type or not message_content:
        return jsonify({"message": "Missing required fields"}), 400

    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    # Permission validation
    if role == 'user' and chat_room.user_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403
    elif role == 'professional' and chat_room.professional_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403

    # Determine recipient_id based on sender's role
    recipient_id = chat_room.professional_id if role == 'user' else chat_room.user_id

    sender_name = "User" if role == 'user' else "Professional"
    new_message = ChatMessage(
        chat_room_id=chat_room_id,
        sender_id=sender_id,
        sender_name=sender_name,
        sender_type=role,
        message_type=message_type,
        message_content=message_content,
        timestamp=datetime.now(),
        msg_id=str(uuid.uuid4()),
        from_uid=sender_id,
        recipient_id=recipient_id,  # Set recipient ID
        receipt=1,  # Default receipt status
    )
    
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully"}), 201

# Create a new chat room
@chat_bp.route('/chats/create', methods=['POST'])
@token_required
def create_chat_room(current_user):
    data = request.get_json()
    user_id = data.get('user_id')
    professional_id = data.get('professional_id')

    if not user_id or not professional_id:
        return jsonify({"message": "User ID and Professional ID are required"}), 400

    chat_room = ChatRoom.query.filter_by(user_id=user_id, professional_id=professional_id).first()
    if chat_room:
        return jsonify({"data": {"chat_room_id": chat_room.id}}), 200

    new_chat_room = ChatRoom(user_id=user_id, professional_id=professional_id, created_at=datetime.now())
    db.session.add(new_chat_room)
    db.session.commit()

    return jsonify({"data": {"chat_room_id": new_chat_room.id}}), 201

# Mark all messages as read in a chat room
@chat_bp.route('/chats/<int:chat_room_id>/read', methods=['POST'])
@token_required
def mark_messages_read(current_user, chat_room_id):
    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    ChatMessage.query.filter_by(chat_room_id=chat_room_id, is_read=False).update({"is_read": True})
    db.session.commit()

    return jsonify({"message": "Messages marked as read"}), 200
