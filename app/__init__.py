from flask import Flask
from .config import Config
from .db import db
from .models import *
from flask_cors import CORS
import logging
from .routes import register_routes
from .socketio import socketio  # ✅ Import global SocketIO
from .services import start_scheduler  # ✅ Import Scheduler

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ✅ Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # ✅ Load configuration
    app.config.from_object(Config)

    # ✅ Initialize the database
    db.init_app(app)

    # ✅ Ensure tables are created
    with app.app_context():
        db.create_all()

    # ✅ Register routes
    register_routes(app)

    # ✅ Attach Socket.IO to Flask app
    socketio.init_app(app)

    # ✅ Start the scheduler
    start_scheduler(app)


    return app
