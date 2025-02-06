from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from ..utils import token_required
from .redis_config import redis_client  # Import Redis

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
@token_required
def handle_connect(current_user):
    user_id = str(current_user.get('user_id'))  # Convert to string for Redis keys
    session_id = request.sid  # Get session ID

    # Store user session in Redis (Set expires in 24 hours)
    redis_client.hset("active_users", user_id, session_id)

    join_room(user_id)  # Join user-specific room
    print(f"User {user_id} connected")

    # Notify all users (optional)
    socketio.emit("user_status_update", {"user_id": user_id, "status": "online"}, broadcast=True)

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
        print(f"User {user_id} disconnected")

        # Notify all users (optional)
        socketio.emit("user_status_update", {"user_id": user_id, "status": "offline"}, broadcast=True)

# Get Active Users API
@app.route('/active_users', methods=['GET'])
def get_active_users():
    active_users = redis_client.hgetall("active_users")  # Get all online users
    return jsonify({"active_users": list(active_users.keys())})
