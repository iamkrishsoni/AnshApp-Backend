from datetime import datetime
from flask import Blueprint, request, jsonify
from ..models import DailyActivity
from ..db import db
from . import token_required

# Blueprint for Mindfulness routes
mindfulness_bp = Blueprint('mindfulness', __name__)

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

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "Mindfulness updated successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
