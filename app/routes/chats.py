from flask import Blueprint, request, jsonify
from ..db import db
from datetime import datetime
from ..models import ChatRoom, ChatMessage

chat_bp = Blueprint('bounty',__name__)

@chat_bp.route('/chats', methods=['GET'])
@token_required
def get_chats():
    user_id = request.user_data.get('user_id')  # Authenticated user's ID
    role = request.user_data.get('role')       # 'user' or 'professional'

    if role == 'user':
        chats = ChatRoom.query.filter_by(user_id=user_id).all()
    elif role == 'professional':
        chats = ChatRoom.query.filter_by(professional_id=user_id).all()
    else:
        return jsonify({"message": "Invalid role"}), 400

    chat_data = []
    for chat in chats:
        last_message = ChatMessage.query.filter_by(chat_room_id=chat.id).order_by(ChatMessage.timestamp.desc()).first()
        chat_data.append({
            "chat_room_id": chat.id,
            "user_id": chat.user_id,
            "professional_id": chat.professional_id,
            "last_message": last_message.message_content if last_message else None,
            "last_message_time": last_message.timestamp if last_message else None
        })

    return jsonify({"chats": chat_data}), 200


@chat_bp.route('/chats/<int:chat_room_id>/message', methods=['POST'])
@token_required
def send_message(chat_room_id):
    data = request.get_json()
    sender_id = request.user_data.get('user_id')  # Authenticated user's ID
    role = request.user_data.get('role')         # 'user' or 'professional'

    # Validate input
    message_type = data.get('message_type')  # 'text', 'image', 'video', 'audio'
    message_content = data.get('message_content')

    if not message_type or not message_content:
        return jsonify({"message": "Message type and content are required"}), 400

    # Validate chat room
    chat_room = ChatRoom.query.get(chat_room_id)
    if not chat_room:
        return jsonify({"message": "Chat room not found"}), 404

    if role == 'user' and chat_room.user_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403
    elif role == 'professional' and chat_room.professional_id != sender_id:
        return jsonify({"message": "Unauthorized"}), 403

    # Create a new message
    new_message = ChatMessage(
        chat_room_id=chat_room_id,
        sender_type=role,
        sender_id=sender_id,
        message_type=message_type,
        message_content=message_content
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully"}), 201

@chat_bp.route('/chats/create', methods=['POST'])
@token_required
def create_chat_room():
    data = request.get_json()
    user_id = data.get('user_id')
    professional_id = data.get('professional_id')

    if not user_id or not professional_id:
        return jsonify({"message": "User ID and Professional ID are required"}), 400

    # Check if chat room exists
    chat_room = ChatRoom.query.filter_by(user_id=user_id, professional_id=professional_id).first()
    if not chat_room:
        chat_room = ChatRoom(user_id=user_id, professional_id=professional_id)
        db.session.add(chat_room)
        db.session.commit()

    return jsonify({"chat_room_id": chat_room.id}), 200