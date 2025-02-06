from flask import Blueprint, request, jsonify
from datetime import datetime, time
from ..models import Goals, User, DailyActivity
from ..db import db
from ..utils import token_required

goal_bp = Blueprint('goal', __name__)

from datetime import datetime, time

@goal_bp.route('/add', methods=['POST'])
@token_required
def add_goal(current_user):
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["title", "type", "start_date", "end_date"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Parse and extract input data
        userid = current_user.get("user_id")
        title = data.get("title")
        description = data.get("description", None)
        image = data.get("image", None)
        goal_type = data.get("type").lower()

        # Convert start_date and end_date if they are in MM/DD/YYYY format
        try:
            start_date = datetime.strptime(data.get("start_date"), "%m/%d/%Y").date()
        except ValueError:
            start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d").date()

        try:
            end_date = datetime.strptime(data.get("end_date"), "%m/%d/%Y").date()
        except ValueError:
            end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d").date()

        # Defaults for time fields
        start_time = None
        end_time = None

        if goal_type == "daily":
            # Require start_time and end_time for daily goals
            if "start_time" not in data or "end_time" not in data:
                return jsonify({"error": "Daily goals require start_time and end_time"}), 400

            # Convert start_time and end_time from 12-hour format (AM/PM) to 24-hour format
            try:
                start_time_str = data.get("start_time")
                end_time_str = data.get("end_time")

                # Convert '01:01 AM' to '01:01:00'
                start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
                end_time = datetime.strptime(end_time_str, "%I:%M %p").time()
            except ValueError as ve:
                return jsonify({"error": f"Invalid time format: {ve}"}), 400
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
        today = datetime.today().strftime('%Y-%m-%d')
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        # If DailyActivity doesn't exist, create one
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  # Set default values as False
                journaling=False,
                mindfulness=False,
                goalsetting=True,
                visionboard=False,  # Mark vision board as completed
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, update visionboard to True
            daily_activity.goalsetting = True
        db.session.commit()

        return jsonify({
            "message": "Goal added successfully",
            "goal": new_goal.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@goal_bp.route('/getall', methods=['GET'])
@token_required
def get_all_goals(current_user):
    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch all goals for the user
        goals = Goals.query.filter_by(userid=user_id).all()

        return jsonify({
            "message": "All goals fetched successfully",
            "goals": [goal.to_dict() for goal in goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@goal_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_goals(current_user):
    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch daily goals for the user
        daily_goals = Goals.query.filter_by(userid=user_id, type="daily").all()

        return jsonify({
            "message": "Daily goals fetched successfully",
            "goals": [goal.to_dict() for goal in daily_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@goal_bp.route('/monthly', methods=['GET'])
@token_required
def get_monthly_goals(current_user):
    """
    Fetch all monthly goals of a user.
    """
    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch monthly goals for the user
        monthly_goals = Goals.query.filter_by(userid=user_id, type="monthly").all()

        return jsonify({
            "message": "Monthly goals fetched successfully",
            "goals": [goal.to_dict() for goal in monthly_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@goal_bp.route('/yearly', methods=['GET'])
@token_required
def get_yearly_goals(current_user):
    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    try:
        # Fetch yearly goals for the user
        yearly_goals = Goals.query.filter_by(userid=user_id, type="yearly").all()

        return jsonify({
            "message": "Yearly goals fetched successfully",
            "goals": [goal.to_dict() for goal in yearly_goals]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@goal_bp.route('/update/<int:goal_id>', methods=['PUT'])
@token_required
def update_goal(current_user, goal_id):
    try:
        data = request.get_json()

        # Fetch the goal by ID and verify ownership
        goal = Goals.query.filter_by(id=goal_id, userid=current_user.get("user_id")).first()
        if not goal:
            return jsonify({"error": "Goal not found or access denied"}), 404

        # Validate input fields (but do NOT allow type change)
        restricted_fields = ["id", "userid", "type"]  # Fields that cannot be changed

        for field in data:
            if field in restricted_fields:
                return jsonify({"error": f"Field '{field}' cannot be modified"}), 400

        # Update only allowed fields
        if "title" in data:
            goal.title = data["title"]
        if "description" in data:
            goal.description = data.get("description", None)
        if "image" in data:
            goal.image = data.get("image", None)

        # Convert and update start_date and end_date if provided
        if "start_date" in data:
            try:
                goal.start_date = datetime.strptime(data["start_date"], "%m/%d/%Y").date()
            except ValueError:
                goal.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        if "end_date" in data:
            try:
                goal.end_date = datetime.strptime(data["end_date"], "%m/%d/%Y").date()
            except ValueError:
                goal.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()

        # Handle start_time and end_time updates for daily goals only
        if goal.type == "daily":
            if "start_time" in data:
                try:
                    goal.start_time = datetime.strptime(data["start_time"], "%I:%M %p").time()
                except ValueError:
                    return jsonify({"error": "Invalid start_time format"}), 400
            if "end_time" in data:
                try:
                    goal.end_time = datetime.strptime(data["end_time"], "%I:%M %p").time()
                except ValueError:
                    return jsonify({"error": "Invalid end_time format"}), 400

        # Commit changes
        db.session.commit()

        return jsonify({
            "message": "Goal updated successfully",
            "goal": goal.to_dict()
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
            "goal": goal.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@goal_bp.route('/delete/<int:goal_id>', methods=['DELETE'])
@token_required
def delete_goal(current_user, goal_id):
    try:
        # Fetch the goal by ID
        goal = Goals.query.filter_by(id=goal_id).first()
        
        if not goal:
            return jsonify({"error": f"Goal with ID {goal_id} not found"}), 404

        # Ensure the current user is the owner of the goal, if applicable (optional step based on business logic)
        if goal.userid != current_user.get('user_id'):
            return jsonify({"error": "Unauthorized access. You can only delete your own goals."}), 403

        # Delete the goal from the database
        db.session.delete(goal)
        db.session.commit()

        return jsonify({
            "message": f"Goal with ID {goal_id} deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
    
    # Print the error to the console
        print(f"Error: {str(e)}")
    
        return jsonify({"error": str(e)}), 500