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

        try:
            # Decode the JWT token
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            request.user_data = data  # Store decoded token data for access in route functions

            # Check if the token is in the expiredTokens table
            # expired_token = ExpiredToken.query.filter_by(token=token).first()
            # if expired_token:
                # return jsonify({'message': 'Token has been expired or logged out!'}), 401
            
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)

    return decorated
