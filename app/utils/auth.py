import jwt
from functools import wraps
from flask import request, jsonify, current_app
from jwt import ExpiredSignatureError, InvalidTokenError
from ..db import db
from ..models import ExpiredToken  # Import your models (assuming SQLAlchemy is being used)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Extract token from 'Bearer <token>'

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        print("Token received:", token)
        
        try:
            # Debugging current_app
            if not current_app:
                raise Exception("No current app context found!")

            secret_key = current_app.config.get('JWT_SECRET_KEY')
            if not secret_key:
                raise Exception("JWT_SECRET_KEY not found in app config!")
            
            print("Decoding token with secret:", secret_key)

            # Decode the JWT token
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            request.user_data = data  # Store decoded token data for access in route functions
            print(" data passing",data)
            # Check if the token is blacklisted (expired or logged out)
            expired_token = ExpiredToken.query.filter_by(token=token).first()
            if expired_token:
                return jsonify({'message': 'Token has been expired or logged out!'}), 401

        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print("Error during token processing:", str(e))
            return jsonify({'message': f'Error processing token: {str(e)}'}), 500

        return f(*args, **kwargs)

    return decorated
