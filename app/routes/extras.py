from datetime import datetime
from flask import Blueprint, request, jsonify
from ..models import DailyActivity
from ..db import db
from . import token_required

# Blueprint for extras routes
extras_bp = Blueprint('extras', __name__)

@extras_bp.route('/add', methods=['POST'])
@token_required
def add_app_usage_time(current_user):
    try:
        # Get today's date
        today = datetime.today().strftime('%Y-%m-%d')

        # Get the app usage time from the request
        data = request.get_json()
        app_usage_time = data.get("app_usage_time")  # Expecting this field in seconds or the desired unit

        if app_usage_time is None:
            return jsonify({"error": "Missing 'app_usage_time' field"}), 400

        # Find the DailyActivity record for the user for today
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        # If DailyActivity doesn't exist, create one with app_usage_time set
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  # Default values as False
                journaling=False,
                mindfulness=False,
                goalsetting=False,
                visionboard=False,
                app_usage_time=app_usage_time  # Set app usage time to the value from the request
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, update app_usage_time by adding the provided value
            daily_activity.app_usage_time += app_usage_time

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "App usage time updated successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
