
from flask import Flask
from .config import Config
from .db import db
from .models import *
from .routes import register_routes
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)


    
    # Ensure the tables are created at the start (in app context)
    with app.app_context():
        db.create_all()

    # Register the routes
    register_routes(app)

    return app
