from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import User, BountyPoints
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from datetime import datetime

user_bp = Blueprint('users', __name__)
bounty_points_bp = Blueprint('bounty_points', __name__)

class UserProfileSchema(Schema):
    user_id = fields.String(required=True)
    role = fields.String(required=True)
    name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    dateOfBirth = fields.String(required=True)
    gender = fields.String(required=True)
    location = fields.String(required=True)

user_schema = UserProfileSchema()

# Update User Profile
@user_bp.route("/users/<int:userid>", methods=["PUT"])
@token_required
def update_user(userid):
    data = request.get_json()

    # Validate input data
    errors = user_schema.validate(data)
    if errors:
        print("Validation errors:", errors)  # Log errors for debugging
        return jsonify(errors), 400

    user = User.query.get(userid)

    # Check if the user exists
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Handle phone number logic
    new_phone = data.get("phone", user.phone)
    if new_phone:
        existing_user_with_phone = User.query.filter(User.phone == new_phone, User.id != userid).first()
        if existing_user_with_phone:
            # If the phone number is already in use, set it to None
            new_phone = None

    # Update user attributes
    user.name = data.get("name", user.name)
    user.surname = data.get("surname", user.surname)
    user.email = data.get("email", user.email)
    user.phone = new_phone
    user.date_of_birth = data.get("dateOfBirth", user.date_of_birth)
    user.gender = data.get("gender", user.gender)
    user.location = data.get("location", user.location)

    try:
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Log the error for debugging
        return jsonify({"message": "An error occurred while updating the user"}), 500

# Delete User Profile
@user_bp.route("/users/<int:userid>", methods=["DELETE"])
@token_required
def delete_user(userid):
    """
    Deletes a user by their user ID.
    """
    user = User.query.get(userid)

    # Check if the user exists
    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Log the error for debugging
        return jsonify({"message": "An error occurred while deleting the user"}), 500



@bounty_points_bp.route("/user/<int:userId>/bountypoints", methods=["PUT"])
@token_required
def update_bounty_points(userId):
    
    data = request.get_json()

    # Validate input
    if not data or 'points' not in data:
        return jsonify({"message": "Invalid input, 'points' field is required"}), 400

    bounty_points = BountyPoints.query.filter_by(user_id=userId).first()

    if not bounty_points:
        return jsonify({"message": "Bounty points for the user not found"}), 404

    try:
        bounty_points.last_added_points = data['points']
        bounty_points.points += int(data['points'])
        bounty_points.date = datetime.now().date()
        db.session.commit()
        return jsonify({"message": "Bounty points updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Debugging
        return jsonify({"message": "An error occurred while updating bounty points"}), 500

# Fetch bounty points for a user
@bounty_points_bp.route("/user/<int:userId>/bountypoints", methods=["GET"])
@token_required
def get_bounty_points(userId):
    
    bounty_points = BountyPoints.query.filter_by(user_id=userId).first()

    if not bounty_points:
        return jsonify({"message": "Bounty points for the user not found"}), 404

    return jsonify({
        "id": bounty_points.id,
        "name": bounty_points.name,
        "category": bounty_points.category,
        "points": bounty_points.points,
        "lastAddedPoints": bounty_points.last_added_points,
        "recommendedPoints": bounty_points.recommended_points,
        "date": bounty_points.date.strftime("%d/%m/%Y")
    }), 200