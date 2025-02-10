from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, jsonify
from .redis_config import redis_client  # Import Redis for active user storage
from .utils import token_required, parse_token
from .models import Notifications
import json
from .db import db

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

@socketio.on("*")
def catch_all_events(event, data):
    print(f"📩 Received Event: {event} with Data: {data}")

@socketio.on("check_redis")
def check_redis(sid=None):  # ✅ Accept an optional session ID
    redis_client.hset("active_users", "42", "ndVO1RuBfqlW5_t6AAAF")
    active_users = redis_client.hgetall("active_users")  # ✅ Get all stored active users
    print(f"📌 Redis Active Users: {active_users}")  # ✅ Debug log
    return {"active_users": active_users}

