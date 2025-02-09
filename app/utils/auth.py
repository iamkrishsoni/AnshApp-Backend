import jwt
from functools import wraps
from flask import request, jsonify, current_app
from jwt import ExpiredSignatureError, InvalidTokenError
from ..db import db
from datetime import datetime
from ..models import ExpiredToken , User # Import your models (assuming SQLAlchemy is being used)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Extract token from 'Bearer <token>'

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            secret_key = current_app.config.get('JWT_SECRET_KEY')
            if not secret_key:
                raise Exception("JWT_SECRET_KEY not found in app config!")

            # Decode the JWT token
            data = jwt.decode(token, secret_key, algorithms=['HS256'])

            # Check if the token is blacklisted (expired or logged out)
            expired_token = ExpiredToken.query.filter_by(token=token).first()
            if expired_token:
                return jsonify({'message': 'Token has been expired or logged out!'}), 401

            # Validate token expiration
            if 'exp' in data:
                expiration = data['exp']
                if expiration < datetime.utcnow().timestamp():
                    return jsonify({'message': 'Token has expired!'}), 401

            # Store user data in the request context and pass it to the decorated function
            current_user = data  # Assuming `data` contains all the necessary user info
            return f(current_user, *args, **kwargs)  # Pass current_user to the route handler

        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print("Error during token processing:", str(e))
            return jsonify({'message': f'Error processing token: {str(e)}'}), 500

    return decorated

def parse_token():
    """Parse and validate the token passed from the frontend."""
    token = request.auth.get('token')  # The token will be in the query string (URL params)

    if not token:
        print("❌ Token not found")
        return None

    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        # Decode the JWT token using the secret key (replace Config.JWT_SECRET_KEY with your secret key)
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")  # Extract user_id or other relevant info

        if not user_id:
            print("❌ Invalid token, user_id not found")
            return None

        # Fetch the user from the database if the token is valid
        current_user = decoded_token

        if not current_user:
            print("❌ User not found")
            return None

        return current_user  # Return the current user object if everything is valid

    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
    except jwt.InvalidTokenError:
        print("❌ Invalid token")

    return None

