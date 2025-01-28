from ..utils import token_required
from flask import Blueprint, request, jsonify, current_app
from ..models import DailyAffirmation, PermanentAffirmation, User, DailyActivity, BountyPoints, BugBountyWallet
from ..db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

affirmation_bp = Blueprint('affirmation', __name__)

# Route for creating Permanent Affirmations
@affirmation_bp.route('/permanent', methods=['POST'])
@token_required
def create_permanent_affirmation(current_user):
    data = request.get_json()
    
    # Extract data from the request
    user_id = current_user.get('user_id')
    affirmation_text = data.get('affirmation_text')
    reminder_active = data.get('reminder_active', False)
    reminder_time = data.get('reminder_time')
    bg_type = data.get('bg_type')  # New field
    bg_image = data.get('bg_image')  # New field
    bg_video = data.get('bg_video')  # New field
    affirmation_type = data.get('affirmation_type')
    isdark = data.get('is_dark')  # New field

    # Fetch the user to ensure it exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Create the PermanentAffirmation object with the new fields
    permanent_affirmation = PermanentAffirmation(
        affirmation_text=affirmation_text,
        user_id=user_id,
        reminder_active=reminder_active,
        reminder_time=reminder_time,
        bg_type=bg_type,
        bg_image=bg_image,
        bg_video=bg_video,
        affirmation_type=affirmation_type,
        isdark=isdark
    )
    try:
        # Add the new affirmation to the session
        db.session.add(permanent_affirmation)
        today = datetime.today().strftime('%Y-%m-%d')
        daily_activity = DailyActivity.query.filter_by(user_id=user_id, date=today).first()

        # If DailyActivity doesn't exist, create one
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=user_id,
                date=today,
                affirmation_completed=True,  # Set affirmation to completed
                journaling=False,
                mindfulness=False,
                goalsetting=False,
                visionboard=False,
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, just update affirmation_completed to True
            daily_activity.affirmation_completed = True

        # Logic for awarding bounty points
        # Check if this is the first time the user creates an affirmation
        first_time_affirmation = not DailyActivity.query.filter_by(user_id=user_id).first()
        if first_time_affirmation:
            bounty_points = BountyPoints(
                user_id=user_id,
                name="Affirmations",
                category="First Time Update",
                points=30,
                recommended_points=30,
                last_added_points=30,
                date=datetime.utcnow()
            )
            db.session.add(bounty_points)
            # Update the user's bounty wallet
            wallet = BugBountyWallet.query.filter_by(user_id=user_id).first()
            if wallet:
                wallet.total_points += 30
                wallet.recommended_points += 30

        # Check for 3 consecutive days of affirmations
        last_three_days = [
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(3)
        ]
        consecutive_activities = DailyActivity.query.filter(
            DailyActivity.user_id == user_id,
            DailyActivity.date.in_(last_three_days),
            DailyActivity.affirmation_completed == True
        ).count()

        if consecutive_activities == 3:
            bounty_points = BountyPoints(
                user_id=user_id,
                name="Affirmations",
                category="3 Day Update",
                points=20,
                recommended_points=20,
                last_added_points=20,
                date=datetime.utcnow()
            )
            db.session.add(bounty_points)
            # Update the user's bounty wallet
            wallet = BugBountyWallet.query.filter_by(user_id=user_id).first()
            if wallet:
                wallet.total_points += 20
                wallet.recommended_points += 20

        # Commit the changes to the database
        db.session.commit()
        return jsonify({"message": "Permanent affirmation created successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

# Route for creating Daily Affirmations
@affirmation_bp.route('/daily', methods=['POST'])
@token_required
def create_daily_affirmation(current_user):
    try:
        data = request.get_json()
        
        user_id = current_user.get('user_id')
        affirmation_text = data.get('affirmation_text')
        reminder_active = data.get('reminder_active', False)
        reminder_time = data.get('reminder_time')
        bg_image = data.get('bg_image')  # Optional background image
        liked = data.get('liked', True)  # Default to False

        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        daily_affirmation = DailyAffirmation(
            affirmation_text=affirmation_text,
            user_id=user_id,
            reminder_active=reminder_active,
            reminder_time=reminder_time,
            bg_image=bg_image,
            liked=liked # Explicitly setting the timestamp
        )

        db.session.add(daily_affirmation)
        db.session.commit()

        return jsonify({
            "message": "Daily affirmation created successfully",
            "affirmation": daily_affirmation.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Database error", "error": str(e)}), 500
    except Exception as e:
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500
# Route for getting Daily Affirmations for a user
@affirmation_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_affirmations(current_user):
    try:
        user_id = current_user.get('user_id')

        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        daily_affirmations = DailyAffirmation.query.filter_by(user_id=user_id).all()
        if not daily_affirmations:
            return jsonify({"message": "No daily affirmations found"}), 404

        return jsonify({
            "message": "Daily affirmations retrieved successfully",
            "affirmations": [aff.to_dict() for aff in daily_affirmations]
        }), 200

    except Exception as e:
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500

# Route for getting Permanent Affirmations for a user
@affirmation_bp.route('/permanent', methods=['GET'])
@token_required
def get_permanent_affirmations(current_user):
    print("current user",current_user)
    userid = current_user.get('user_id')
    user = User.query.get(userid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    permanent_affirmations = PermanentAffirmation.query.filter_by(user_id=userid).all()
    if not permanent_affirmations:
        return jsonify({"message": "No permanent affirmations found"}), 404

    affirmations_list = [{
        "id": aff.id,
        "affirmation_text": aff.affirmation_text,
        "reminder_active": aff.reminder_active,
        "reminder_time": aff.reminder_time,
        "bg_type": aff.bg_type,
        "bg_image": aff.bg_image,
        "bg_video": aff.bg_video,
        "affirmation_type": aff.affirmation_type,
        "isDark": aff.isdark
    } for aff in permanent_affirmations]
    print(affirmations_list)

    return jsonify(affirmations_list), 200

@affirmation_bp.route('/permanent/<int:id>', methods=['PUT'])
@token_required
def update_permanent_affirmation(current_user, id):
    # Get the data from the request
    data = request.get_json()
    
    # Retrieve the user ID from the current_user object
    userid = current_user.get('user_id')
    
    # Find the user in the database
    user = User.query.get(userid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Find the permanent affirmation by ID and user ID
    affirmation = PermanentAffirmation.query.filter_by(id=id, user_id=userid).first()
    if not affirmation:
        return jsonify({"message": "Affirmation not found"}), 404

    # Update the fields if they exist in the request data
    affirmation.affirmation_text = data.get('affirmation_text', affirmation.affirmation_text)
    affirmation.reminder_active = data.get('reminder_active', affirmation.reminder_active)
    affirmation.reminder_time = data.get('reminder_time', affirmation.reminder_time)
    affirmation.bg_type = data.get('bg_type', affirmation.bg_type)
    affirmation.bg_image = data.get('bg_image', affirmation.bg_image)
    affirmation.bg_video = data.get('bg_video', affirmation.bg_video)
    affirmation.affirmation_type = data.get('affirmation_type', affirmation.affirmation_type)
    affirmation.isdark = data.get('isDark', affirmation.isdark)

    # Commit the changes to the database
    try:
        db.session.commit()
        return jsonify({"message": "Permanent affirmation updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@affirmation_bp.route('/permanent/<int:id>', methods=['DELETE'])
@token_required
def delete_permanent_affirmation(current_user, id):
    # Retrieve the user ID from the current_user object
    userid = current_user.get('user_id')

    # Find the permanent affirmation by ID and user ID
    affirmation = PermanentAffirmation.query.filter_by(id=id, user_id=userid).first()
    if not affirmation:
        return jsonify({"message": "Affirmation not found"}), 404

    # Delete the affirmation from the database
    try:
        db.session.delete(affirmation)
        db.session.commit()
        return jsonify({"message": "Permanent affirmation deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@affirmation_bp.route('/daily/<int:id>', methods=['PUT'])
@token_required
def update_daily_affirmation(current_user, id):
    try:
        data = request.get_json()
        user_id = current_user.get('user_id')

        daily_affirmation = DailyAffirmation.query.filter_by(id=id, user_id=user_id).first()
        if not daily_affirmation:
            return jsonify({"message": "Affirmation not found"}), 404

        # Update fields if provided
        daily_affirmation.affirmation_text = data.get("affirmation_text", daily_affirmation.affirmation_text)
        daily_affirmation.bg_image = data.get("bg_image", daily_affirmation.bg_image)
        daily_affirmation.reminder_active = data.get("reminder_active", daily_affirmation.reminder_active)
        daily_affirmation.reminder_time = data.get("reminder_time", daily_affirmation.reminder_time)
        daily_affirmation.liked = data.get("liked", daily_affirmation.liked)
        daily_affirmation.updated_at = datetime.utcnow()  # Update the timestamp

        db.session.commit()
        return jsonify({"message": "Daily affirmation updated successfully", "affirmation": daily_affirmation.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the affirmation", "error": str(e)}), 500

@affirmation_bp.route('/daily/<int:id>', methods=['DELETE'])
@token_required
def delete_daily_affirmation(current_user, id):
    try:
        user_id = current_user.get('user_id')

        daily_affirmation = DailyAffirmation.query.filter_by(id=id, user_id=user_id).first()
        if not daily_affirmation:
            return jsonify({"message": "Affirmation not found"}), 404

        db.session.delete(daily_affirmation)
        db.session.commit()
        return jsonify({"message": "Daily affirmation deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while deleting the affirmation", "error": str(e)}), 500
