from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask
from .config import Config
from .db import db
from .models import *
from .routes import register_routes
from flask_cors import CORS



def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Set up rate limiter
   

    with app.app_context():
        db.create_all()  

    register_routes(app)  

    return app
