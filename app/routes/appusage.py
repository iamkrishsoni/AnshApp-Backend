from flask import Blueprint, request, jsonify
from ..models import AppUsage
from ..db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from ..utils import token_required

# Define a Blueprint for app usage routes
app_usage_bp = Blueprint("app_usage", __name__)

# Route to add a new app usage entry or update if it already exists
@app_usage_bp.route("/add", methods=["POST"])
def add_app_usage():
    try:
        data = request.json
        user_id = data.get("user_id")
        time_spent = data.get("time_spent", 0)  # Time in seconds
        usage_type = data.get("usage_type", "foreground")  # Default to foreground
        date_str = data.get("date")  # Date provided by user (expected format: YYYY-MM-DD)

        # Validate user_id and time_spent
        if not user_id or time_spent < 0:
            return jsonify({"error": "Invalid user_id or time_spent"}), 400

        # Validate and convert the date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400

        # Check if a record exists for the user on this date
        app_usage = AppUsage.query.filter_by(user_id=user_id, date=date).first()

        if app_usage:
            app_usage.time_spent += time_spent  # Update time spent
        else:
            app_usage = AppUsage(
                user_id=user_id,
                date=date,
                time_spent=time_spent,
                usage_type=usage_type,
            )
            db.session.add(app_usage)

        db.session.commit()
        return jsonify({
            "message": "App usage added/updated successfully.",
            "user_id": user_id,
            "date": str(date),
            "total_time_spent": app_usage.time_spent
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Route to update a specific app usage entry
@app_usage_bp.route("/update/<int:id>", methods=["PUT"])
def update_app_usage(id):
    try:
        data = request.json
        time_spent = data.get("time_spent")  # Optional
        usage_type = data.get("usage_type")  # Optional

        app_usage = AppUsage.query.get(id)
        if not app_usage:
            return jsonify({"error": "App usage entry not found."}), 404

        # Update the fields if provided in the request
        if time_spent is not None:
            app_usage.time_spent = time_spent
        if usage_type:
            app_usage.usage_type = usage_type

        db.session.commit()
        return jsonify({"message": "App usage updated successfully."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Route to get app usage entries for a specific user or all users
@app_usage_bp.route("/get", methods=["GET"])
@token_required
def get_app_usage(current_user):
    try:
        user_id = current_user.get('user_id') # Optional

        query = AppUsage.query
        if user_id:
            query = query.filter_by(user_id=user_id)

        app_usages = query.all()
        return jsonify([usage.to_dict() for usage in app_usages]), 200

    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


# Route to delete a specific app usage entry
@app_usage_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_app_usage(id):
    try:
        app_usage = AppUsage.query.get(id)
        if not app_usage:
            return jsonify({"error": "App usage entry not found."}), 404

        db.session.delete(app_usage)
        db.session.commit()
        return jsonify({"message": "App usage deleted successfully."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
