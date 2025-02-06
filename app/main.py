from app import create_app
from .socketio import socketio  # Import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=6000, debug=True)
