from flask import Blueprint, request, jsonify
from ..models import AppUsage
from ..db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Define a Blueprint for app usage routes
app_usage_bp = Blueprint("app_usage", __name__)

# Route to add a new app usage entry or update if it already exists
@app_usage_bp.route("/add", methods=["POST"])
def add_app_usage():
    try:
        data = request.json
        user_id = data.get("user_id")
        time_spent = data.get("time_spent", 0)  # Time spent in seconds
        usage_type = data.get("usage_type", "foreground")  # Default to "foreground"
        date = datetime.utcnow().date()

        # Check if the record already exists for the user and date
        app_usage = AppUsage.query.filter_by(user_id=user_id, date=date).first()

        if app_usage:
            # Update the existing record by adding time_spent
            app_usage.time_spent += time_spent
        else:
            # Create a new record if it doesn't exist
            app_usage = AppUsage(
                user_id=user_id,
                date=date,
                time_spent=time_spent,
                usage_type=usage_type,
            )
            db.session.add(app_usage)

        db.session.commit()
        return jsonify({"message": "App usage added/updated successfully."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
def get_app_usage():
    try:
        user_id = request.args.get("user_id")  # Optional
        date = request.args.get("date")  # Optional, format: YYYY-MM-DD

        query = AppUsage.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if date:
            query = query.filter_by(date=datetime.strptime(date, "%Y-%m-%d").date())

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
