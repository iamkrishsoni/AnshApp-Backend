from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Set up rate limiter
    limiter = Limiter(
        app,
        key_func=get_remote_address,  # Identify clients by their IP addresses
        default_limits=["1000 per second"],  # Global rate limit
    )

    with app.app_context():
        db.create_all()  

    register_routes(app)  

    return app
