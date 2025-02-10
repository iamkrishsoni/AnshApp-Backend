from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask import request, jsonify
from .redis_config import redis_client  # Import Redis for active user storage
from .utils import token_required, parse_token
from .models import Notifications, ChatRoom, ChatMessage, MessageAttachment
import json
import uuid
from .db import db
from datetime import datetime

# ✅ Create a global SocketIO instance (Attach in `app.py`)
socketio = SocketIO(cors_allowed_origins="*")

@socketio.on("connect")
def handle_connect():
    """Handle the WebSocket connection."""
    print(f"🚀 New connection request received. SID: {request.sid}")
    user_id = request.args.get("user_id","42")
    print("user id in soket", user_id)
    try:
        # Store the active user session in Redis
        redis_client.hset("active_users",user_id, request.sid)
        join_room(user_id)
        print(f"✅ User {user_id} connected and added to Redis.")

    except Exception as e:
        print(f"❌ Error during connection: {e}")
        socketio.emit('error', {'message': str(e)}, room=request.sid)
        return False  # Ensures the connection does not proceed if there's an error

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid

    # Find user by session_id
    user_id = None
    for uid, sid in redis_client.hgetall("active_users").items():
        if sid == session_id:
            user_id = uid
            break

    if user_id:
        redis_client.hdel("active_users", user_id)  # Remove from Redis
        leave_room(user_id)
        print(f"❌ User {user_id} disconnected")

        # Notify all users (optional)
        socketio.emit("user_status_update", {"user_id": user_id, "status": "offline"}, broadcast=True)

@socketio.on("custom_event")
def handle_custom_event(data):
    """Handle a custom event sent from the frontend."""
    user_id = data.get("user_id")
    message = data.get("message")

    # Send message to a specific user
    if user_id:
        emit("receive_message", {"message": message}, room=user_id)

# ✅ Function to Send a Real-Time Notification to a Specific User
def send_realtime_notification(user_id, notification):
    """Emit a real-time notification to a specific user if online."""
    if redis_client.hexists("active_users", str(user_id)):  # Check if user is online
        socketio.emit("new_notification", notification, room=user_id)
        print(f"📢 Real-time notification sent to user {user_id}")
    else:
        print(f"⚠️ User {user_id} is offline. Notification not sent in real-time.")

# ✅ API Route to Send a Notification to Any User (Dynamic)
@socketio.on("send_notification")
def send_notification(data):
    print(f"🚀 Received send_notification event with Data: {data}")  # ✅ Debug log
    if isinstance(data, str):  
        data = json.loads(data)
    user_id = data.get("user_id")  
    title = data.get("title", "New Notification")
    message = data.get("message", "You have a new update!")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    new_notification = Notifications(
        title=title,
        description=message,
        user_id=user_id,
        type="info",
        service="Anshap",
        status="pending",
        is_read=False,
        navigation="",
        body="No body for now",
        image=""
    )
    db.session.add(new_notification)
    db.session.commit()

    send_realtime_notification(user_id, notification=new_notification.to_dict())

    # return jsonify({"message": f"Notification sent to user {user_id}"}), 200


@socketio.on('join_chat')
def handle_join_chat(data):
    if isinstance(data, str):
        data = json.loads(data)
    room_id = data.get('chatroom_id')
    user_id = data.get('user_id')

    if not room_id or not user_id:
        return jsonify({'error': 'chatroom_id and user_id are required'}), 400

    # Check if the room exists, create it if it doesn't
    chat_room = ChatRoom.query.filter_by(id=room_id).first()
    # if not chat_room:
    #     chat_room = ChatRoom(id=room_id, user_id=user_id, professional_id=user_id)
    #     db.session.add(chat_room)
    #     db.session.commit()
    join_room(room_id)
    print(f"User {user_id} joined room {room_id}")
    emit('user_joined', {'message': f'User {user_id} joined the chat room.'}, room=room_id)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    if isinstance(data, str):
        data = json.loads(data)
    room_id = data.get('chatroom_id')
    user_id = data.get('user_id')

    if not room_id or not user_id:
        return jsonify({'error': 'chatroom_id and user_id are required'}), 400

    # Leave the room
    leave_room(room_id)
    print(f"User {user_id} left room {room_id}")
    emit('user_left', {'message': f'User {user_id} left the chat room.'}, room=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    print("📩 Received message event:", data)

    try:
        if isinstance(data, str):
            data = json.loads(data)

        sender_id = data.get('sender_id')
        role = data.get('role')
        message_type = data.get('message_type', 'TEXT').upper()
        file_url = data.get('file_url', '')
        message_content = data.get('message_content', '')

        if not sender_id or not role or not message_type:
            emit('error', {"message": "Missing required fields"})
            return

        chat_room_id = data.get('chat_room_id')
        chat_room = ChatRoom.query.get(chat_room_id)
        print("chatroom", chat_room.user_id)

        if not chat_room:
            print("❌ Chat room not found")
            emit('error', {"message": "Chat room not found"})
            return

        # Ensure the sender is in the room
        # join_room(chat_room_id)

        # Check authorization
        if (role == 'user' and chat_room.user_id != sender_id) or \
           (role == 'professional' and chat_room.professional_id != sender_id):
            print('unauthorized')
            emit('error', {"message": "Unauthorized"})
            return

        recipient_id = chat_room.professional_id if role == 'user' else chat_room.user_id
        sender_name = "User" if role == 'user' else "Professional"

        # Validate message type
        if message_type == 'TEXT' and not message_content:
            emit('error', {"message": "Text content is required for TEXT messages"})
            return
        elif message_type != 'TEXT' and not file_url:
            emit('error', {"message": f"File URL is required for {message_type} messages"})
            return

        # Save message in database
        new_message = ChatMessage(
            chat_room_id=chat_room_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_type=role,
            message_type=message_type,
            message_content=message_content if message_type == 'TEXT' else None,
            timestamp=datetime.now(),
            msg_id=str(uuid.uuid4()),
            from_uid=sender_id,
            recipient_id=recipient_id,
            receipt=1,
        )

        db.session.add(new_message)
        db.session.commit()

        # Save attachments if needed
        if message_type != 'TEXT':
            attachment = MessageAttachment(
                chat_message_id=new_message.id,
                attachment_type=message_type,
                url=file_url,
                file_name=file_url.split("/")[-1],
                file_size=0,
            )
            db.session.add(attachment)
            db.session.commit()

        # Emit to the room
        emit('new_message', {
            "message": "Message sent successfully",
            "message_id": new_message.msg_id,
            "chat_room_id": chat_room_id,
            "sender_id": sender_id,
            "message_type": message_type,
            "message_content": message_content,
            "file_url": file_url,
            "timestamp": new_message.timestamp.isoformat(),
            "sender_name": sender_name,
            "user":{
                "_id":sender_id,
                "name":sender_name
            }
        }, room=chat_room_id)

        print(f"✅ Message emitted to room {chat_room_id}")

    except json.JSONDecodeError:
        emit('error', {"message": "Invalid JSON format"})
    except Exception as e:
        print(f"❌ Exception: {e}")
        emit('error', {"message": "Unexpected error", "error": str(e)})

@socketio.on('message')
def handle_message(data):
    """ This event handles basic messages sent with the default message event. """
    emit('message', {'data': data}, broadcast=True)

@socketio.on('send_attachment')
def handle_send_attachment(data):
    """ Handle media file attachments sent by the client. """
    # Save the attachment in the database and emit to the room
    chatroom_id = data.get('chatroom_id')
    message = ChatMessage.from_message_data(data, chatroom_id)

    # Handle attachments
    if 'attachments' in data:
        for attachment_data in data['attachments']:
            attachment = MessageAttachment.from_attachment_data(attachment_data, message.id)
            db.session.add(attachment)

    db.session.commit()

    # Emit the message with media to the room
    emit('new_message', message.to_dict(), room=chatroom_id)
# Optional: Send notifications to users in a room when a new message arrives
def send_notification_to_room(room_id, message_data):
    send(message_data, room=room_id)

@socketio.on("*")
def catch_all_events(event, data):
    print(f"📩 Received Event: {event} with Data: {data}")

@socketio.on("check_redis")
def check_redis(sid=None):  # ✅ Accept an optional session ID
    redis_client.hset("active_users", "42", "ndVO1RuBfqlW5_t6AAAF")
    active_users = redis_client.hgetall("active_users")  # ✅ Get all stored active users
    print(f"📌 Redis Active Users: {active_users}")  # ✅ Debug log
    return {"active_users": active_users}

