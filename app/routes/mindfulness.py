from datetime import datetime
from flask import Blueprint, request, jsonify
from ..models import DailyActivity, Mindfulness
from ..db import db
from ..utils import token_required

# Blueprint for Mindfulness routes
mindfulness_bp = Blueprint('mindfulness', __name__)

# Route for adding a new mindfulness activity
@mindfulness_bp.route('/add', methods=['POST'])
@token_required
def add_mindfulness(current_user):
    try:
        # Get today's date
        today = datetime.today().strftime('%Y-%m-%d')

        # Find the DailyActivity record for the user for today
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        # If DailyActivity doesn't exist, create one with mindfulness set to True
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  # Default values as False
                journaling=False,
                mindfulness=True,  # Set mindfulness to True
                goalsetting=False,
                visionboard=False,
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, update mindfulness to True
            daily_activity.mindfulness = True

        # Now add the mindfulness activity
        data = request.get_json()
        mindfulness_activity = Mindfulness(
            user_id=current_user.get('user_id'),
            title=data.get('title'),
            description=data.get('description'),
            image=data.get('image'),
            audio=data.get('audio'),
            color=data.get('color'),
            additionalinfo=data.get('additionalinfo')
        )

        # Add mindfulness activity to the session
        db.session.add(mindfulness_activity)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "Mindfulness added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mindfulness_bp.route('/get', methods=['GET'])
@token_required
def get_mindfulness(current_user):
    try:
        # Fetch all mindfulness activities for the current user
        mindfulness_activities = Mindfulness.query.filter_by(user_id=current_user.get('user_id')).all()

        # If no mindfulness activities are found
        if not mindfulness_activities:
            return jsonify({"message": "No mindfulness activities found."}), 404

        # Convert each mindfulness activity to a dictionary
        mindfulness_list = [activity.to_dict() for activity in mindfulness_activities]

        return jsonify({"mindfulness_activities": mindfulness_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for updating an existing mindfulness activity by ID
@mindfulness_bp.route('/update/<int:id>', methods=['PUT'])
@token_required
def update_mindfulness(current_user, id):
    try:
        # Find the mindfulness activity by ID and user ID
        mindfulness_activity = Mindfulness.query.filter_by(id=id, user_id=current_user.get('user_id')).first()

        if not mindfulness_activity:
            return jsonify({"message": "Mindfulness activity not found"}), 404

        # Get updated data from the request
        data = request.get_json()
        mindfulness_activity.title = data.get('title', mindfulness_activity.title)
        mindfulness_activity.description = data.get('description', mindfulness_activity.description)
        mindfulness_activity.image = data.get('image', mindfulness_activity.image)
        mindfulness_activity.audio = data.get('audio', mindfulness_activity.audio)
        mindfulness_activity.color = data.get('color', mindfulness_activity.color)
        mindfulness_activity.additionalinfo = data.get('additionalinfo', mindfulness_activity.additionalinfo)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "Mindfulness updated successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for deleting a mindfulness activity by ID
@mindfulness_bp.route('/delete/<int:id>', methods=['DELETE'])
@token_required
def delete_mindfulness(current_user, id):
    try:
        # Find the mindfulness activity by ID and user ID
        mindfulness_activity = Mindfulness.query.filter_by(id=id, user_id=current_user.get('user_id')).first()

        if not mindfulness_activity:
            return jsonify({"message": "Mindfulness activity not found"}), 404

        # Delete the mindfulness activity
        db.session.delete(mindfulness_activity)
        
        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "Mindfulness deleted successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
