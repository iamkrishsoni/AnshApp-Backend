from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import User, BountyPoints, BugBountyWallet
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



@user_bp.route("/user/<int:userId>/bountypoints", methods=["POST"])
@token_required
def update_bounty_points(userId):
    try:
        data = request.get_json()

        wallet_id = data.get('wallet_id')
        category = data.get('category')
        points = data.get('points')
        name = data.get('name')  # Include 'name' explicitly

        # Validate input
        if not all([wallet_id, category, points, name]):
            return jsonify({'error': 'All fields (wallet_id, name, category, points) are required'}), 400

        # Ensure points is an integer
        try:
            points = int(points)
        except ValueError:
            return jsonify({'error': "'points' must be an integer"}), 400

        # Check if a record already exists for the user, wallet, and category
        bounty = BountyPoints.query.filter_by(wallet_id=wallet_id, user_id=userId, category=category).first()

        if bounty:
            # Update existing record
            bounty.points += points
            bounty.last_added_points = points
            bounty.date = datetime.utcnow()
        else:
            # Create a new record
            bounty = BountyPoints(
                wallet_id=wallet_id,
                user_id=userId,
                name=name,  # Ensure 'name' is set
                category=category,
                points=points,
                recommended_points=0,  # Default or calculated value
                last_added_points=points,
                date=datetime.utcnow()
            )
            db.session.add(bounty)

        # Commit the changes
        db.session.commit()
        return jsonify({'message': 'Bounty points updated successfully'}), 200

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        print(f"Error: {e}")  # Log the error for debugging
        return jsonify({'error': 'An error occurred while updating bounty points'}), 500
    

# Fetch bounty points for a user
@user_bp.route("/user/<int:userId>/bountypoints", methods=["GET"])
@token_required
def get_bounty_points(userId):
    # Fetch all bounty points for the user
    bounty_points = BountyPoints.query.filter_by(user_id=userId).all()

    if not bounty_points:
        return jsonify({"message": "No bounty points found for the user"}), 404

    # Return all records for the user
    result = [
        {
            "id": bp.id,
            "name": bp.name,
            "wallet_id": bp.wallet_id,
            "category": bp.category,
            "points": bp.points,
            "lastAddedPoints": bp.last_added_points,
            "recommendedPoints": bp.recommended_points,
            "date": bp.date.strftime("%d/%m/%Y"),
        }
        for bp in bounty_points
    ]

    return jsonify(result), 200

@user_bp.route("/user/<int:userId>/bountywallet", methods=["GET"])
@token_required
def get_bounty_wallet(userId):
    try:
        # Query the wallet for the user
        wallet = BugBountyWallet.query.filter_by(user_id=userId).first()

        if not wallet:
            return jsonify({"message": "Bug Bounty Wallet not found for the user"}), 404

        # Calculate total points for the wallet from related BountyPoints
        total_points = db.session.query(db.func.sum(BountyPoints.points)) \
                                  .filter_by(wallet_id=wallet.id) \
                                  .scalar() or 0  # Default to 0 if no points
        total_recommended_points = db.session.query(db.func.sum(BountyPoints.recommended_points)) \
                                             .filter_by(wallet_id=wallet.id) \
                                             .scalar() or 0  # Default to 0 if no recommended points

        # Update wallet totals (optional, to keep it in sync)
        wallet.total_points = total_points
        wallet.recommended_points = total_recommended_points
        db.session.commit()

        return jsonify({
            "wallet_id": wallet.id,
            "user_id": wallet.user_id,
            "total_points": wallet.total_points,
            "recommended_points": wallet.recommended_points,
            "bounty_details": [
                {
                    "category": bp.category,
                    "points": bp.points,
                    "last_added_points": bp.last_added_points,
                    "date": bp.date.strftime("%d/%m/%Y"),
                }
                for bp in wallet.bounty_points
            ],
        }), 200

    except Exception as e:
        print(f"Error: {e}")  # Log the error for debugging
        return jsonify({'error': 'An error occurred while fetching the wallet'}), 500
