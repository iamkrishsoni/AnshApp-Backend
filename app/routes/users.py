from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import User, BountyPoints, BugBountyWallet, DailyActivity, BountyMilestone
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from datetime import datetime
from sqlalchemy.sql import func
from collections import defaultdict

user_bp = Blueprint('users', __name__)
bounty_points_bp = Blueprint('bounty_points', __name__)

class UserProfileSchema(Schema):
    user_id = fields.String(required=True)
    role = fields.String(required=True)
    user_name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(allow_none=True, validate=validate.Length(min=10, max=15))
    dateOfBirth = fields.String(required=True)
    user_gender = fields.String(required=True)
    location = fields.String(required=True)
    avatar = fields.String(required=False)

user_schema = UserProfileSchema()

# Update User Profile
@user_bp.route("/users", methods=["PUT"])  # No need for <int:userid> in the route
@token_required
def update_user(current_user):
    if not current_user:
        return jsonify({"message": "Unauthorized access"}), 401

    userid = current_user.get('user_id')  # Assuming `current_user` contains the user ID
    data = request.get_json()

    # Validate input data
    # errors = user_schema.validate(data)
    # if errors:
    #     print("Validation errors:", errors)  # Log errors for debugging
    #     return jsonify(errors), 400

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
    user.user_name = data.get("user_name", user.user_name)
    user.surname = data.get("surname", user.surname)
    user.email = data.get("email", user.email)
    user.phone = new_phone
    user.date_of_birth = data.get("dateOfBirth", user.date_of_birth)
    user.user_gender = data.get("user_gender", user.user_gender)
    user.location = data.get("location", user.location)
    user.avatar = data.get("avatar", user.avatar)
    user.hashed_password = data.get("password", user.hashed_password)

    try:
        db.session.commit()

        # Fetch associated wallet and bounty points
        bug_bounty_wallet = BugBountyWallet.query.filter_by(user_id=user.id).first()
        bounty_points = [
            {
                "id": point.id,
                "name": point.name,
                "category": point.category,
                "points": point.points,
                "date": point.date.strftime("%Y-%m-%d")
            }
            for point in bug_bounty_wallet.bounty_points
        ] if bug_bounty_wallet else []

        # Return updated user data in the required format
        return jsonify({
            "message": "User updated successfully",
            "user": user.to_dict(),  # Convert user object to dictionary
            "bugBountyWallet": {
                "totalPoints": bug_bounty_wallet.total_points if bug_bounty_wallet else 0,
                "recommendedPoints": bug_bounty_wallet.recommended_points if bug_bounty_wallet else 0,
                "bountyPoints": bounty_points
            }
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the user"}), 500


@user_bp.route("/avatar", methods=["PUT"])  # Specific route for avatar update
@token_required
def update_user_avatar(current_user):
    if not current_user:
        return jsonify({"message": "Unauthorized access"}), 401

    userid = current_user.get('user_id')  # Assuming `current_user` contains the user ID
    data = request.get_json()
    new_avatar = data.get("avatar")

    # Validate input
    if not new_avatar:
        return jsonify({"message": "Avatar URL is required"}), 400

    user = User.query.get(userid)

    # Check if the user exists
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Update the avatar field
    user.avatar = new_avatar

    try:
        db.session.commit()
        updated_user = User.query.get(userid)

        # Fetch associated wallet and bounty points
        bug_bounty_wallet = BugBountyWallet.query.filter_by(user_id=user.id).first()
        bounty_points = [
            {
                "id": point.id,
                "name": point.name,
                "category": point.category,
                "points": point.points,
                "date": point.date.strftime("%Y-%m-%d")
            }
            for point in bug_bounty_wallet.bounty_points
        ] if bug_bounty_wallet else []

        # Return updated user data in the required format
        return jsonify({
            "message": "Avatar updated successfully",
            "user": updated_user.to_dict(),  # Convert user object to dictionary
            "bugBountyWallet": {
                "totalPoints": bug_bounty_wallet.total_points if bug_bounty_wallet else 0,
                "recommendedPoints": bug_bounty_wallet.recommended_points if bug_bounty_wallet else 0,
                "bountyPoints": bounty_points
            }
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Log the error for debugging
        return jsonify({"message": "An error occurred while updating the avatar"}), 500

# Delete User Profile
@user_bp.route("/users", methods=["DELETE"])
@token_required
def delete_user(current_user):
    """
    Deletes a user by their user ID.
    """
    userid = current_user.get('user_id')
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

@user_bp.route("/users/onboarding", methods=["PATCH"])
@token_required
def update_onboarding_status(current_user):
    if not current_user:
        return jsonify({"message": "Unauthorized access"}), 401

    userid = current_user.get('user_id')  # Assuming `current_user` contains the user ID
    data = request.get_json()
    
    # Validate input data
    onboarding_field = data.get("onboarding_field")
    if onboarding_field not in ["affirmation_onboarding", "journaling_onboarding", "visionboard_onboarding", "app_onboarding", "buddy_onboarding"]:
        return jsonify({"message": "Invalid onboarding field"}), 400

    # Retrieve the user
    user = User.query.get(userid)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Set the relevant onboarding field to True
    setattr(user, onboarding_field, True)

    try:
        db.session.commit()

        return jsonify({
            "message": f"{onboarding_field} updated successfully",
            "user": user.to_dict()  # Convert user object to dictionary
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")  # Log the error for debugging
        return jsonify({"message": "An error occurred while updating the onboarding status"}), 500


@user_bp.route("/user/bountypoints", methods=["POST"])
@token_required
def update_bounty_points(current_user):
    try:
        data = request.get_json()
        userId = current_user.get('user_id')

        wallet_id = data.get('wallet_id')
        category = data.get('category')
        points = data.get('points')
        name = data.get('name')

        if not all([wallet_id, category, points, name]):
            return jsonify({'error': 'All fields (wallet_id, name, category, points) are required'}), 400

        try:
            points = int(points)
        except ValueError:
            return jsonify({'error': "'points' must be an integer"}), 400

        month = datetime.utcnow().strftime('%m-%Y')
        today = datetime.utcnow().date()

        existing_bounty = BountyPoints.query.filter_by(
            wallet_id=wallet_id, user_id=userId, category=category, month=month
        ).filter(func.date(BountyPoints.date) == today).first()

        if existing_bounty:
            return jsonify({'error': 'Bounty points for this category have already been added today'}), 409

        bounty = BountyPoints.query.filter_by(wallet_id=wallet_id, user_id=userId, category=category, month=month).first()

        if bounty:
            bounty.points += points
            bounty.last_added_points = points
            bounty.date = datetime.utcnow()
        else:
            bounty = BountyPoints(
                wallet_id=wallet_id,
                user_id=userId,
                name=name,
                category=category,
                points=points,
                recommended_points=0,
                last_added_points=points,
                month=month,
                date=datetime.utcnow()
            )
            db.session.add(bounty)

        db.session.commit()
        return jsonify({'message': 'Bounty points updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while updating bounty points'}), 500

@user_bp.route("/user/bountypoints", methods=["GET"])
@token_required
def get_bounty_points(current_user):
    userId = current_user.get('user_id')
    bounty_points = (
        db.session.query(
            BountyPoints.month,
            BountyPoints.category,
            func.sum(BountyPoints.points).label("total_points"),
            func.sum(BountyPoints.recommended_points).label("total_recommended")
        )
        .filter(BountyPoints.user_id == userId)
        .group_by(BountyPoints.month, BountyPoints.category)
        .order_by(BountyPoints.month)
        .all()
    )

    result = defaultdict(lambda: {"total_points": 0, "categories": {}})
    for bp in bounty_points:
        result[bp.month]["total_points"] += bp.total_points
        result[bp.month]["categories"][bp.category] = {
            "points": bp.total_points,
            "recommended_points": bp.total_recommended
        }

    return jsonify(result), 200

@user_bp.route("/user/bountywallet", methods=["GET"])
@token_required
def get_bounty_wallet(current_user):
    userId = current_user.get('user_id')
    try:
        wallet = BugBountyWallet.query.filter_by(user_id=userId).first()

        if not wallet:
            return jsonify({"message": "Bug Bounty Wallet not found for the user"}), 404

        # Group points by month
        monthly_points = (
            db.session.query(
                BountyPoints.month,
                func.sum(BountyPoints.points).label("total_points"),
                func.sum(BountyPoints.recommended_points).label("total_recommended")
            )
            .filter(BountyPoints.wallet_id == wallet.id)
            .group_by(BountyPoints.month)
            .order_by(BountyPoints.month.desc())
            .all()
        )

        # Structure response
        result = {
            "wallet_id": wallet.id,
            "user_id": wallet.user_id,
            "monthly_data": {}
        }

        for mp in monthly_points:
            result["monthly_data"][mp.month] = {
                "total_points": mp.total_points,
                "recommended_points": mp.total_recommended,
                "bountyPoints": [
                    {
                        "category": bp.category,
                        "points": bp.points,
                        "last_added_points": bp.last_added_points,
                        "date": bp.date.strftime("%d/%m/%Y"),
                    }
                    for bp in wallet.bounty_points if bp.month == mp.month
                ],
            }

        return jsonify(result), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching the wallet'}), 500

@user_bp.route("/milestone/claim", methods=["POST"])
@token_required
def claim_milestone(current_user):
    user_id = current_user.get('user_id')
    data = request.get_json()
    milestone = data.get("milestone")

    # Validate milestone value
    valid_milestones = {1000, 2500, 5000, 10000}
    if milestone not in valid_milestones:
        return jsonify({"error": "Invalid milestone value"}), 400

    # Get the current month and year
    current_month = datetime.utcnow().strftime("%Y-%m")

    # Calculate the total points earned by the user for the month
    user_points = (
        db.session.query(func.sum(BountyPoints.points))
        .filter(
            BountyPoints.user_id == user_id,
            func.to_char(BountyPoints.date, "YYYY-MM") == current_month  # Updated this line
        )
        .scalar() or 0
    )

    # Check if the user has achieved the milestone
    if user_points < milestone:
        return jsonify({"error": f"User has only {user_points} points this month, milestone {milestone} not achieved"}), 400

    # Check if milestone is already claimed for this month
    record = BountyMilestone.query.filter_by(user_id=user_id, milestone=milestone).first()

    if record and record.claimed:
        return jsonify({"error": f"Milestone {milestone} already claimed"}), 400

    try:
        if not record:
            # If no record exists, create a new one
            record = BountyMilestone(
                user_id=user_id,
                milestone=milestone,
                claimed=True,
                date_achieved=datetime.utcnow()
            )
            db.session.add(record)
        else:
            # Otherwise, mark it as claimed
            record.claimed = True
        
        db.session.commit()

        return jsonify({
            "message": f"Milestone {milestone} points reward claimed!",
            "milestone": milestone,
            "claimed": True,
            "date_claimed": record.date_achieved.strftime("%d/%m/%Y"),
        }), 200

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while claiming the milestone"}), 500

@user_bp.route("/milestones", methods=["GET"])
@token_required
def get_user_milestones(current_user):
    user_id = current_user.get('user_id')

    milestones = BountyMilestone.query.filter_by(user_id=user_id).all()

    result = [
        {
            "milestone": m.milestone,
            "claimed": m.claimed,
            "date_achieved": m.date_achieved.strftime("%d/%m/%Y"),
        }
        for m in milestones
    ]

    return jsonify(result), 200

@user_bp.route('/get-daily-activities', methods=['GET'])
@token_required
def get_daily_activities(current_user):
    user_id = current_user.get('user_id')  # Get the user ID from the query parameters

    # Ensure user_id is provided
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400

    # Fetch user from the database
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Fetch all daily activities for the user
    daily_activities = DailyActivity.query.filter_by(user_id=user_id).all()

    # Return the data as a list of dictionaries
    activities_data = [activity.to_dict() for activity in daily_activities]
    print(activities_data)
    
    return jsonify(activities_data), 200

def can_add_bounty_points(user_id, new_points, date):
    month = date.strftime("%Y-%m")

    # Get total points for the month
    total_monthly_points = (
        db.session.query(func.sum(BountyPoints.points))
        .filter(
            BountyPoints.user_id == user_id,
            func.strftime("%Y-%m", BountyPoints.date) == month
        )
        .scalar() or 0  # Default to 0 if no points found
    )

    # Check if adding new points exceeds the limit
    return (total_monthly_points + new_points) <= 10000

def check_milestone_achievements(user_id):
    total_points = (
        db.session.query(func.sum(BountyPoints.points))
        .filter_by(user_id=user_id)
        .scalar() or 0
    )

    milestones = [1000, 2500, 5000, 10000]
    achieved_milestones = (
        db.session.query(BountyMilestone.milestone)
        .filter(BountyMilestone.user_id == user_id, BountyMilestone.claimed == False)
        .all()
    )
    
    achieved_milestones = {m[0] for m in achieved_milestones}

    for milestone in milestones:
        if total_points >= milestone and milestone not in achieved_milestones:
            new_milestone = BountyMilestone(
                user_id=user_id,
                milestone=milestone,
                claimed=False
            )
            db.session.add(new_milestone)

    db.session.commit()
