from flask import Blueprint, request, jsonify
from datetime import datetime, time
from ..models import Goals
from ..db import db
from ..utils import token_required

goal_bp = Blueprint('goal', __name__)

@goal_bp.route('/add', methods=['POST'])
@token_required
def add_goal(current_user):
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["userid", "title", "type", "start_date", "end_date"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Parse and extract input data
        userid = data.get("userid")
        title = data.get("title")
        description = data.get("description", None)
        image = data.get("image", None)
        goal_type = data.get("type").lower()
        start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d").date()
        end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d").date()

        # Defaults for time fields
        start_time = None
        end_time = None

        if goal_type == "daily":
            # Require start_time and end_time for daily goals
            if "start_time" not in data or "end_time" not in data:
                return jsonify({"error": "Daily goals require start_time and end_time"}), 400
            start_time = datetime.strptime(data.get("start_time"), "%H:%M:%S").time()
            end_time = datetime.strptime(data.get("end_time"), "%H:%M:%S").time()
        elif goal_type in ["monthly", "yearly"]:
            # Set default times for monthly and yearly goals
            start_time = time(0, 0, 0)  # Midnight
            end_time = time(23, 59, 59)  # End of the day
        else:
            return jsonify({"error": f"Invalid goal type: {goal_type}"}), 400

        # Create and save the goal
        new_goal = Goals(
            userid=userid,
            title=title,
            description=description,
            image=image,
            type=goal_type,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(new_goal)
        db.session.commit()

        return jsonify({
            "message": "Goal added successfully",
            "goal": new_goal.__todict()
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@goal_bp.route('/getall', methods=['GET'])
@token_required
def get_all_goals(current_user):
    user_id = request.args.get('userid')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch all goals for the user
        goals = Goals.query.filter_by(userid=user_id).all()

        return jsonify({
            "message": "All goals fetched successfully",
            "goals": [goal.__todict() for goal in goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@goal_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_goals(current_user):
    user_id = request.args.get('userid')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch daily goals for the user
        daily_goals = Goals.query.filter_by(userid=user_id, type="daily").all()

        return jsonify({
            "message": "Daily goals fetched successfully",
            "goals": [goal.__todict() for goal in daily_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@goal_bp.route('/monthly', methods=['GET'])
@token_required
def get_monthly_goals(current_user):
    """
    Fetch all monthly goals of a user.
    """
    user_id = request.args.get('userid')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch monthly goals for the user
        monthly_goals = Goals.query.filter_by(userid=user_id, type="monthly").all()

        return jsonify({
            "message": "Monthly goals fetched successfully",
            "goals": [goal.__todict() for goal in monthly_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@goal_bp.route('/yearly', methods=['GET'])
@token_required
def get_yearly_goals(current_user):
    user_id = request.args.get('userid')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch yearly goals for the user
        yearly_goals = Goals.query.filter_by(userid=user_id, type="yearly").all()

        return jsonify({
            "message": "Yearly goals fetched successfully",
            "goals": [goal.__todict() for goal in yearly_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@goal_bp.route('/<int:goal_id>/status', methods=['PATCH'])
@token_required
def update_goal_status(current_user,goal_id):
    try:
        # Parse the request data
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Missing 'status' in request body"}), 400

        # Fetch the goal by ID
        goal = Goals.query.filter_by(id=goal_id).first()
        if not goal:
            return jsonify({"error": f"Goal with ID {goal_id} not found"}), 404

        # Update the status
        new_status = data['status']
        goal.status = new_status

        # Commit the changes to the database
        db.session.commit()

        return jsonify({
            "message": "Goal status updated successfully",
            "goal": goal.__todict()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
