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
        today = datetime.today().strftime('%Y-%m-%d')

        data = request.get_json()
        app_usage_time = data.get("app_usage_time") 

        if app_usage_time is None:
            return jsonify({"error": "Missing 'app_usage_time' field"}), 400

        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  
                journaling=False,
                mindfulness=False,
                goalsetting=False,
                visionboard=False,
                app_usage_time=app_usage_time  
            )
            db.session.add(daily_activity)
        else:
            daily_activity.app_usage_time += app_usage_time

        db.session.commit()
        return jsonify({"message": "App usage time updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
